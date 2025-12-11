from pydantic import BaseModel
from typing import List

class HRItem(BaseModel):
    id: str
    category: str
    problem: str
    solution: str

class HRExtractionResult(BaseModel):
    items: List[HRItem]
