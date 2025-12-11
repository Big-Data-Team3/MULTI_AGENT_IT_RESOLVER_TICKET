import os
import time
from pathlib import Path

from dotenv import load_dotenv
from llama_parse import LlamaParse
from openai import OpenAI


# -----------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

if not LLAMA_CLOUD_API_KEY:
    raise RuntimeError("LLAMA_CLOUD_API_KEY is not set in .env")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -----------------------------------------------------------
# Caption generator using GPT-4o-mini
# -----------------------------------------------------------
def caption_image(image_path: str) -> str:
    if client is None:
        return "(Image description unavailable: OPENAI_API_KEY not set.)"

    with open(image_path, "rb") as f:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text",
                         "text": "Describe this image in 2–3 lines."},
                        {"type": "input_image", "image": f},
                    ],
                }
            ],
        )

    return resp.choices[0].message["content"]


# -----------------------------------------------------------
# MAIN PARSER (using 2025 LlamaParse Preset System)
# -----------------------------------------------------------
def parse_pdf_with_captions(pdf_path: Path, start_page_num: int = 1) -> Path:
    t0 = time.time()
    pdf_name = pdf_path.stem
    print(f"\n[{pdf_name}] Starting parse...\n")

    # Output paths
    OUT_DIR = Path("parsed_output")
    pdf_out = OUT_DIR / pdf_name
    images_dir = pdf_out / "images"

    pdf_out.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    # -------------------------------------------------------
    # NEW (2025): LlamaParse using preset + output_format
    # -------------------------------------------------------
    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        preset="high_res",               # <── best for troubleshooting PDFs
        output_format=["markdown"],      # <── no JSON
        include_images=True,             # <── extract images
    )

    # Parse document
    result = parser.parse(str(pdf_path))

    # Page-by-page markdown
    markdown_pages = result.get_markdown_documents(split_by_page=True)

    # Extract image objects
    try:
        image_docs = result.get_image_documents(
            include_screenshot_images=True,
            include_object_images=True,
            image_download_dir=str(images_dir),
        )
    except Exception as e:
        print("[WARNING] Failed to get images:", e)
        image_docs = []

    # Map page → images
    page_to_images = {}

    for img in image_docs:
        meta = getattr(img, "metadata", None)
        if not meta:
            continue

        page_num = getattr(meta, "page", None)
        if page_num is None and isinstance(meta, dict):
            page_num = meta.get("page", 1)

        page_num = int(page_num or 1)

        # Determine image path
        img_path = None
        if hasattr(img, "image_path") and img.image_path:
            img_path = img.image_path
        elif hasattr(img, "file_path") and img.file_path:
            img_path = img.file_path
        elif hasattr(img, "file") and img.file:  # raw bytes fallback
            fname = f"page_{page_num}_{len(page_to_images.get(page_num, []))}.png"
            img_path = images_dir / fname
            with open(img_path, "wb") as f:
                f.write(img.file)
        else:
            continue

        page_to_images.setdefault(page_num, []).append(str(img_path))

    # -------------------------------------------------------
    # Build combined markdown
    # -------------------------------------------------------
    combined_md_parts = []

    for i, page_doc in enumerate(markdown_pages):
        page_number = start_page_num + i

        combined_md_parts.append(f"___\n\n# Page {page_number}\n\n")
        combined_md_parts.append(page_doc.text.strip())

        # Caption images
        if page_number in page_to_images:
            for img_path in page_to_images[page_number]:
                img_file = os.path.basename(img_path)
                rel_path = f"images/{img_file}"

                print(f"Captioning image: {img_file} (Page {page_number})")
                caption = caption_image(img_path)

                combined_md_parts.append(
                    f"\n\n![]({rel_path})\n\n> **Image Description:** {caption}\n"
                )

    # Save markdown
    md_path = pdf_out / f"{pdf_name}.md"
    md_path.write_text("\n".join(combined_md_parts), encoding="utf-8")

    # Save text version (optional)
    text_docs = result.get_text_documents(split_by_page=False)
    if text_docs:
        (pdf_out / f"{pdf_name}.txt").write_text(
            text_docs[0].text, encoding="utf-8"
        )

    print(f"\n[{pdf_name}] COMPLETE — {len(result.pages)} pages processed in {time.time() - t0:.1f}s")
    print(f"Output saved to: {pdf_out}\n")

    return pdf_out


# -----------------------------------------------------------
# ENTRYPOINT: Process all PDFs in set_1
# -----------------------------------------------------------
if __name__ == "__main__":
    INPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "pdf" / "set_3"

    if not INPUT_DIR.exists():
        raise RuntimeError(f"Folder not found: {INPUT_DIR}")

    pdf_files = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() == ".pdf"]

    print(f"Found {len(pdf_files)} PDF(s) in {INPUT_DIR}\n")

    for pdf_path in pdf_files:
        try:
            print(f"---- Parsing: {pdf_path.name} ----")
            parse_pdf_with_captions(pdf_path)
        except Exception as e:
            print(f"\n[ERROR] Failed: {pdf_path.name}: {e}\n")
            continue

    print("\nAll processing complete.")





