import yaml
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from pathlib import Path

# Resolve project root (one level above src/)
ROOT_DIR = Path(__file__).resolve().parent.parent

# YAML lives at root level
YAML_PATH = ROOT_DIR / "dol_fact_sheets.yaml"

# Output markdown directory at root level
OUTPUT_DIR = ROOT_DIR / "data" / "dol_fact_sheets_md"
OUTPUT_DIR.mkdir(exist_ok=True)


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

    # Fact sheets typically store content inside <main>
    main = soup.find("main") or soup.find("div", class_="region-content")
    if not main:
        print("⚠ Warning: Could not find <main>. Using full HTML fallback.")
        main = soup

    # Remove non-content tags
    for tag in main.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Convert HTML to markdown
    return md(str(main), heading_style="ATX")


def save_markdown(name, text):
    out_path = OUTPUT_DIR / f"{name}.md"
    out_path.write_text(text, encoding="utf-8")
    print(f"Saved → {out_path}")


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
            print(f"❌ Error scraping {name}: {e}")


if __name__ == "__main__":
    scrape()
