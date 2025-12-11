import instructor
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

from hr.models_hr import HRExtractionResult
from hr.prompt_hr import SYSTEM_PROMPT_HR

# Composer already injects environment variables; no need for .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize client for OpenAI (NO Azure)
client = instructor.patch(
    OpenAI(api_key=OPENAI_API_KEY)
)


def extract_from_hr_markdown(filename: str, markdown: str) -> HRExtractionResult:
    """
    Calls OpenAI via Instructor to extract structured HR policy data.
    """

    user_prompt = f"""
Extract HR regulatory knowledge from this DOL fact sheet.

FILENAME: {filename}

CONTENT:
{markdown}
"""

    result = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_HR},
            {"role": "user", "content": user_prompt},
        ],
        response_model=HRExtractionResult,
    )

    return result
