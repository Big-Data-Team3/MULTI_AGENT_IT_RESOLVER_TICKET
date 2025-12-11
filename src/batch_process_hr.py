import json
import os
from pathlib import Path
from google.cloud import storage

from hr.extractor_hr import extract_from_hr_markdown


# --------------------------------------------------------------------
# Environment Variables Required in Composer
# --------------------------------------------------------------------
# HR_MD_PREFIX = "gs://<bucket>/data/dol_fact_sheets_md/"
# HR_OUTPUT_PATH = "gs://<bucket>/knowledge_base/knowledge_base_HRPL.json"
# --------------------------------------------------------------------

GCS_MD_PREFIX = os.environ["HR_MD_PREFIX"]
GCS_OUTPUT_PATH = os.environ["HR_OUTPUT_PATH"]

storage_client = storage.Client()


# -----------------------------
# GCS Helper Functions
# -----------------------------

def list_md_files():
    """Returns a list of Blob objects for all .md files in the prefix."""
    bucket_name = GCS_MD_PREFIX.replace("gs://", "").split("/")[0]
    prefix = "/".join(GCS_MD_PREFIX.replace("gs://", "").split("/")[1:])

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    md_blobs = [b for b in blobs if b.name.endswith(".md")]
    return md_blobs


def read_md(blob):
    """Downloads a Markdown file from GCS."""
    return blob.download_as_text(encoding="utf-8")


def write_output_to_gcs(json_data: str):
    """Writes the final JSON output to GCS."""
    bucket_name = GCS_OUTPUT_PATH.replace("gs://", "").split("/")[0]
    blob_path = "/".join(GCS_OUTPUT_PATH.replace("gs://", "").split("/")[1:])

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(json_data, content_type="application/json")

    print(f"Knowledge Base uploaded → gs://{bucket_name}/{blob_path}")


# -----------------------------
# Main Extractor
# -----------------------------

def extract_all_hr():
    """Runs extraction for all markdown files in the GCS MD folder."""
    md_blobs = list_md_files()
    print(f"Found {len(md_blobs)} HR markdown files.\n")

    all_items = []
    counter = 1

    for blob in md_blobs:
        filename = Path(blob.name).name
        print(f"=== Extracting from {filename} ===")

        markdown = read_md(blob)

        try:
            hr_result = extract_from_hr_markdown(filename, markdown)

            for item in hr_result.items:
                item.id = f"PL-{counter:06d}"
                counter += 1
                all_items.append(item.model_dump())

            print(f" -> Extracted {len(hr_result.items)} items\n")

        except Exception as e:
            print(f"Error processing {filename}: {e}\n")

    # Convert all extracted items to JSON
    json_text = json.dumps(all_items, indent=2)

    # Upload JSON back to GCS
    write_output_to_gcs(json_text)

    print("HR Knowledge Base extraction complete!")


if __name__ == "__main__":
    extract_all_hr()
