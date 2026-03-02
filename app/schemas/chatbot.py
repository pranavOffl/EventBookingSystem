from pydantic import BaseModel, Field
from typing import List

class ChatRequest(BaseModel):
    query: str = Field(default="Hi, how are you?")

class ChatResponse(BaseModel):
    response: str

class IntentClassification(BaseModel):
    intent: str = Field(description="The categorized intent")

class DecomposedQueries(BaseModel):
    queries: List[str] = Field(description="List of cleaned and decomposed individual queries. Returns precisely ['other'] if entirely unrelated.")

class Reflection(BaseModel):
    grade: str = Field(description="Must be exactly 'Pass' if AI is successful, or a detailed string critique if it failed.")
