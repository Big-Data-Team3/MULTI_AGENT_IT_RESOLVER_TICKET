import json
from google.cloud import storage
import os
from datetime import datetime

# Bucket name
BUCKET_NAME = "us-central1-it-agent-resolv-bd0fece4-bucket"
LOG_FOLDER = "logs"

def get_gcs_client():
    return storage.Client()

def save_chat_log(session_id, data):
    """Saves logs to a GCS bucket instead of local file system."""
    client = get_gcs_client()
    bucket = client.bucket(BUCKET_NAME)

    blob_path = f"{LOG_FOLDER}/{session_id}.json"
    blob = bucket.blob(blob_path)

    blob.upload_from_string(
        json.dumps(data, indent=4),
        content_type="application/json"
    )

    print(f"Log saved to GCS: gs://{BUCKET_NAME}/{blob_path}")

def create_message(role, content):
    return {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }




