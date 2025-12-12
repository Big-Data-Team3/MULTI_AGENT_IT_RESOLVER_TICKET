import json
from google.cloud import storage

# Initialize client once
storage_client = storage.Client()

def list_logs(bucket_name: str, prefix: str = "logs/"):
    """
    Returns list of .json files inside GCS folder.
    """
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    files = [blob.name for blob in blobs if blob.name.endswith(".json")]
    return {"files": files}


def load_log_file(bucket_name: str, file_path: str):
    """
    Loads ONE log file from GCS and returns parsed JSON.
    """
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    try:
        content = blob.download_as_bytes()
        return {"file_path": file_path, "content": json.loads(content)}
    except Exception as e:
        return {"error": str(e)}
