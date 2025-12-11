# batch_process_it.py

import json
import os
from google.cloud import storage
from pathlib import Path

from it.extractor_it import extract_from_markdown


# Lazy-load env variables
def get_env():
    return {
        "PREFIX": os.environ["IT_MD_PREFIX"],
        "OUTPUT": os.environ["IT_OUTPUT_PATH"]
    }


storage_client = storage.Client()


def list_markdown_blobs(prefix: str):
    bucket = prefix.replace("gs://", "").split("/")[0]
    folder = "/".join(prefix.replace("gs://", "").split("/")[1:])

    b = storage_client.bucket(bucket)
    return [blob for blob in b.list_blobs(prefix=folder) if blob.name.endswith(".md")]


def read_md(blob):
    return blob.download_as_text()


def write_output_json(output_path: str, json_text: str):
    bucket = output_path.replace("gs://", "").split("/")[0]
    path = "/".join(output_path.replace("gs://", "").split("/")[1:])

    b = storage_client.bucket(bucket)
    blob = b.blob(path)
    blob.upload_from_string(json_text, content_type="application/json")

    print(f"✔ Uploaded IT KB → {output_path}")


def extract_all_it():
    env = get_env()
    prefix = env["PREFIX"]
    output_path = env["OUTPUT"]

    blobs = list_markdown_blobs(prefix)
    print(f"Found {len(blobs)} markdown files.")

    all_items = []
    counter = 1

    for blob in blobs:
        filename = Path(blob.name).name
        print(f"\n=== Extracting → {filename}")

        md_text = read_md(blob)

        try:
            result = extract_from_markdown(filename, md_text)
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue

        for item in result.items:
            item.id = f"itcb-{counter:06d}"
            counter += 1
            all_items.append(item.model_dump())

    # Upload final JSON to GCS
    write_output_json(output_path, json.dumps(all_items, indent=2))

    print("🎉 IT KB Extraction complete!")


if __name__ == "__main__":
    extract_all_it()
