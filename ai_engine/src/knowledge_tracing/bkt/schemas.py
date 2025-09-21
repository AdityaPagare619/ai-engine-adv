# ai_engine/src/knowledge_tracing/bkt/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any

class TraceRequest(BaseModel):
    student_id: str = Field(..., description="UUID of the student")
    concept_id: str = Field(..., description="Unique concept ID")
    question_id: Optional[str] = Field(None, description="Question ID providing context")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")

    # Optional override/context hints (for logging/analysis; not required for core math)
    difficulty_level: Optional[str] = Field(None, description="Editorial difficulty label, if any")
    bloom_level: Optional[str] = Field(None, description="Bloom taxonomy level, if any")
    
    # Added fields for intervention system
    difficulty: float = Field(0.5, ge=0.0, le=1.0, description="Question difficulty from 0 to 1")
    time_pressure: float = Field(0.0, ge=0.0, le=1.0, description="Time pressure level from 0 to 1")

    @field_validator("student_id", "concept_id")
    @classmethod
    def non_empty(cls, v: str):
        assert isinstance(v, str) and len(v) > 0, "must be non-empty"
        return v

class InterventionData(BaseModel):
    strategy: str = Field(..., description="Name of the intervention strategy")
    level: str = Field(..., description="Level of intervention (NONE, MILD, MODERATE, STRONG, CRITICAL)")
    recommendations: list = Field(..., description="List of specific recommendations")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of intervention success")

class TraceResponse(BaseModel):
    previous_mastery: float = Field(..., ge=0.0, le=1.0)
    posterior_mastery: float = Field(..., ge=0.0, le=1.0)
    new_mastery: float = Field(..., ge=0.0, le=1.0)
    p_correct_pred: float = Field(..., ge=0.0, le=1.0)

    adjusted_params: Dict[str, float] = Field(
        ..., description="Final feasible learn_rate, slip_rate, guess_rate used for update"
    )
    constraint_violations: list = Field(default_factory=list)
    explanation: Dict[str, Any] = Field(default_factory=dict)
    intervention: Optional[InterventionData] = Field(None, description="Intervention data if performance decline detected")

class EvaluateWindowRequest(BaseModel):
    concept_id: Optional[str] = Field(None, description="Limit evaluation to this concept")
    start_ts: Optional[str] = Field(None, description="ISO start time filter")
    end_ts: Optional[str] = Field(None, description="ISO end time filter")
    # Future: filters by cohort, subject, ability bands

class EvaluateWindowResponse(BaseModel):
    next_step_auc: float = Field(..., ge=0.0, le=1.0)
    next_step_accuracy: float = Field(..., ge=0.0, le=1.0)
    brier_score: float = Field(..., ge=0.0, le=1.0)
    calibration_error: float = Field(..., ge=0.0, le=1.0)
    trajectory_validity: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    details: Dict[str, Any] = Field(default_factory=dict)
