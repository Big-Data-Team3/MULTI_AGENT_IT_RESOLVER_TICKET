import json
from google.cloud import storage

def load_logs_from_gcs(bucket_name: str, prefix: str = "logs/"):
    """
    Loads all .json logs from a GCS bucket folder and returns them as Python objects.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=prefix)
    logs = []

    for blob in blobs:
        if blob.name.endswith(".json"):
            try:
                content = blob.download_as_bytes()
                logs.append(json.loads(content))
            except Exception as e:
                print(f"Failed to load {blob.name}: {e}")

    return logs
