# ai_engine/src/knowledge_tracing/pacing/schemas.py
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime

class TimeAllocationRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    base_time_ms: int = Field(..., gt=0)
    stress_level: float = Field(..., ge=0.0, le=1.0)
    fatigue_level: float = Field(..., ge=0.0, le=1.0)
    mastery: float = Field(..., ge=0.0, le=1.0)
    difficulty: float = Field(..., ge=0.0)
    session_elapsed_ms: int = Field(..., ge=0)

class TimeAllocationResponse(BaseModel):
    student_id: str
    question_id: str
    final_time_ms: int
    factor: float
    breakdown: Dict[str, float]
    timestamp: datetime
