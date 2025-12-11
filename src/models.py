# models.py
from pydantic import BaseModel
from typing import List

class KBItem(BaseModel):
    id: str               # e.g. itcb-temp (real IDs added later)
    category: str         # Azure Logic Apps, Windows Drivers, etc.
    problem: str          # Short title
    solution: str         # Merged Symptoms + Cause + Steps + Resolution

class KBExtractionResult(BaseModel):
    items: List[KBItem]
