import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "dataset_output.jsonl")
OUTPUT_DIR = os.path.join(BASE_DIR, "knowledge_base")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hr_dataset.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------------------------
# Extract problem & solution from messages[]
# -------------------------------------------
def extract_user_and_assistant(row):
    user_msg = ""
    assistant_msg = ""

    for msg in row.get("messages", []):
        if msg.get("role") == "user":
            user_msg = msg.get("content", "")
        elif msg.get("role") == "assistant":
            assistant_msg = msg.get("content", "")

    return user_msg.strip(), assistant_msg.strip()


# -------------------------------------------
# LLM classification
# -------------------------------------------
def classify_with_llm(text: str) -> str:
    prompt = f"""
You are an HR issue classifier.

Given the employee question below, return ONLY a JSON object:

{{
  "category": "<one best category>"
}}

Categories:
- Payroll Issue
- Leave / Time-Off Request
- Benefits / Insurance Inquiry
- HR Policy Question
- Employee Relations Concern
- Workplace Safety Issue
- Hiring / Onboarding Request
- Offboarding / Exit Process
- Employment Verification
- General HR Inquiry

Employee question:
\"\"\"{text}\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        data = json.loads(json_str)
        return data.get("category", "General HR Inquiry")
    except:
        return "General HR Inquiry"


# -------------------------------------------
# Process dataset
# -------------------------------------------
output_records = []

print(f"[INFO] Reading dataset → {INPUT_FILE}")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, start=1):
        row = json.loads(line)

        problem, solution = extract_user_and_assistant(row)

        record_id = f"hr-{idx:03d}"

        print(f"[INFO] Classifying record {record_id}...")

        category = classify_with_llm(problem)

        output_records.append({
            "id": record_id,
            "category": category,
            "problem": problem,
            "solution": solution,
        })


# -------------------------------------------
# Save output
# -------------------------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    json.dump(output_records, out, indent=4, ensure_ascii=False)

print(f"[SUCCESS] Created {OUTPUT_FILE}")
