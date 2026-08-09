from pydantic import BaseModel, Field
from typing import List, Literal

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: List[Message] = []

class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=1)
