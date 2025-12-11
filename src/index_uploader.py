import os
import json
from google.cloud import storage
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from azure.search.documents import SearchClient
from openai import AzureOpenAI


# ---------------- LAZY ENV VAR LOADER ----------------
def load_env():
    return {
        "GCS_PREFIX": os.getenv("KB_GCS_PREFIX"),
        "VECTOR_DIM": int(os.getenv("VECTOR_DIM", "3072")),
        "SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "SEARCH_KEY": os.getenv("AZURE_SEARCH_KEY"),
        "SEARCH_INDEX": os.getenv("AZURE_SEARCH_INDEX"),
        "AOAI_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AOAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AOAI_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    }


# ---------------- HELPER INITIALIZATION ----------------
def get_clients():
    env = load_env()

    storage_client = storage.Client()
    credential = AzureKeyCredential(env["SEARCH_KEY"])

    index_client = SearchIndexClient(
        endpoint=env["SEARCH_ENDPOINT"],
        credential=credential
    )

    search_client = SearchClient(
        endpoint=env["SEARCH_ENDPOINT"],
        index_name=env["SEARCH_INDEX"],
        credential=credential
    )

    openai_client = AzureOpenAI(
        api_key=env["AOAI_KEY"],
        azure_endpoint=env["AOAI_ENDPOINT"],
        api_version="2025-01-01-preview"
    )

    return env, storage_client, index_client, search_client, openai_client


# ---------------- GCS HELPERS ----------------
def list_kb_json_files(storage_client, gcs_prefix):
    bucket = gcs_prefix.replace("gs://", "").split("/")[0]
    prefix = "/".join(gcs_prefix.replace("gs://", "").split("/")[1:])

    b = storage_client.bucket(bucket)

    return [
        blob for blob in b.list_blobs(prefix=prefix)
        if blob.name.endswith(".json")
    ]


def load_json(blob):
    return json.loads(blob.download_as_text())


# ---------------- BATCH UPLOAD ----------------
def upload_in_batches(search_client, docs, batch_size=100):
    print(f"Uploading {len(docs)} documents in batches of {batch_size} ...")
    for i in range(0, len(docs), batch_size):
        chunk = docs[i:i+batch_size]
        print(f" → Uploading batch {i//batch_size + 1} ({len(chunk)} docs)")
        search_client.upload_documents(documents=chunk)


# ---------------- AZURE SEARCH ----------------
def create_index_if_not_exists(index_client, env):
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="problem", type=SearchFieldDataType.String),
        SearchableField(name="solution", type=SearchFieldDataType.String),

        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=env["VECTOR_DIM"],
            vector_search_profile_name="default"
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="default")],
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="default")]
    )

    index = SearchIndex(
        name=env["SEARCH_INDEX"],
        fields=fields,
        vector_search=vector_search
    )

    try:
        index_client.get_index(env["SEARCH_INDEX"])
        print(f"Index exists → {env['SEARCH_INDEX']}")
    except Exception:
        print("Creating new index...")
        index_client.create_index(index)
        print("Index created")


# ---------------- EMBEDDINGS ----------------
def embed(openai_client, text, deployment):
    response = openai_client.embeddings.create(
        input=[text],
        model=deployment
    )
    return response.data[0].embedding


# ---------------- MAIN PIPELINE ----------------
def run_indexing_pipeline():
    env, storage_client, index_client, search_client, openai_client = get_clients()

    create_index_if_not_exists(index_client, env)

    blobs = list_kb_json_files(storage_client, env["GCS_PREFIX"])
    print(f"Found {len(blobs)} KB JSON files to upload.")

    enriched_docs = []

    for blob in blobs:
        print(f"Processing {blob.name} ...")
        data = load_json(blob)

        for record in data:
            record["embedding"] = embed(openai_client, record["problem"], env["AOAI_DEPLOYMENT"])
            enriched_docs.append(record)

    print("Uploading documents...")
    upload_in_batches(search_client, enriched_docs)
    print("Indexing Complete.")
