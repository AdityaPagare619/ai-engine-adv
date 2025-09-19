from pydantic import BaseModel, Field
from typing import Optional

class TraceRequest(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    concept_id: str = Field(..., description="Unique concept ID")
    question_id: Optional[str] = Field(None, description="Question ID for context")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    difficulty_level: Optional[str] = Field(None, description="Question difficulty level")
    bloom_level: Optional[str] = Field(None, description="Bloom taxonomy level")

class TraceResponse(BaseModel):
    previous_mastery: float = Field(..., ge=0.0, le=1.0)
    new_mastery: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    learning_occurred: bool
    explanation: dict = Field(default_factory=dict, description="Detailed explanation of the update")
    question_context: Optional[dict] = Field(None, description="Question metadata used")
