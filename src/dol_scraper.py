import yaml
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from pathlib import Path
import os

# Optional import for GCS upload
from google.cloud import storage


# Resolve directory structure based on environment

# Composer mode: GCS output bucket is provided
GCS_OUTPUT = os.environ.get("SCRAPER_OUTPUT_BUCKET")

# Local mode: preserve your old structure
ROOT_DIR = Path(__file__).resolve().parent
YAML_PATH = ROOT_DIR / "dol_fact_sheets.yaml"
LOCAL_OUTPUT_DIR = ROOT_DIR / "data" / "dol_fact_sheets_md"

# Create local output folder if running locally
if not GCS_OUTPUT:
    LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Utility Functions


def load_yaml():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_html(url):
    print(f"Downloading: {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_main_content(html):
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find("main") or soup.find("div", class_="region-content")
    if not main:
        print("Warning: Could not find <main>. Using full HTML fallback.")
        main = soup

    for tag in main.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    return md(str(main), heading_style="ATX")



# Save Markdown (Local or GCS)


def save_markdown(name, text):
    filename = f"{name}.md"


    # 1. Cloud Composer (GCS upload mode)

    if GCS_OUTPUT and GCS_OUTPUT.startswith("gs://"):
        bucket_name = GCS_OUTPUT.replace("gs://", "").split("/")[0]
        prefix_parts = GCS_OUTPUT.replace("gs://", "").split("/")[1:]
        prefix = "/".join(prefix_parts).rstrip("/")

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        blob_path = f"{prefix}/{filename}"
        blob = bucket.blob(blob_path)

        blob.upload_from_string(text, content_type="text/markdown")

        print(f"Uploaded to GCS → gs://{bucket_name}/{blob_path}")
        return


    # 2. Local mode (normal file save)

    out_path = LOCAL_OUTPUT_DIR / filename
    out_path.write_text(text, encoding="utf-8")
    print(f"Saved locally → {out_path}")



# Main Scraper Logic


def scrape():
    config = load_yaml()
    items = config.get("dol_fact_sheets", [])

    print(f"Found {len(items)} fact sheets.\n")

    for item in items:
        name = item["name"]
        url = item["url"]

        try:
            html = fetch_html(url)
            md_text = extract_main_content(html)
            save_markdown(name, md_text)

        except Exception as e:
            print(f"Error scraping {name}: {e}")


if __name__ == "__main__":
    scrape()
