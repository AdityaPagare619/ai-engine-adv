from pydantic import BaseModel, Field

class TraceRequest(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    concept_id: str = Field(..., description="Unique concept ID")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time_ms: int = Field(None, description="Response time in milliseconds")

class TraceResponse(BaseModel):
    previous_mastery: float = Field(..., ge=0.0, le=1.0)
    new_mastery: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    learning_occurred: bool
