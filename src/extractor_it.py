# extractor_it.py

import instructor
from openai import OpenAI
from it.models import KBExtractionResult
from it.prompt import SYSTEM_PROMPT

import os

# Environment vars provided by Composer
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize Instructor/OpenAI client
client = instructor.patch(
    OpenAI(api_key=OPENAI_API_KEY)
)


def extract_from_markdown(filename: str, markdown: str) -> KBExtractionResult:
    """Extract troubleshooting issues from markdown using LLM."""
    user_prompt = f"""
Extract all troubleshooting issues from this markdown and return KBExtractionResult.

FILENAME: {filename}

CONTENT:
{markdown}
"""

    result = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_model=KBExtractionResult,
    )

    return result
