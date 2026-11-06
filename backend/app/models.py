from pydantic import BaseModel, Field
from typing import List, Literal

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: List[Message] = []
    # Omit this to use the bundled demo profile. An uploaded resume gets its
    # own ID, preventing one browser's upload from becoming another's profile.
    candidate_id: str | None = None

class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=1)
    candidate_id: str | None = None
