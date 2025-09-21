# ai_engine/src/admin/exam_config_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

from ..config.exam_config import EXAM_CONFIGS, ExamConfiguration, ScoringScheme

router = APIRouter()

class MarkingSchemeUpdateRequest(BaseModel):
    exam_code: str
    correct_score: float
    incorrect_score: float
    partial_credit_rules: Optional[Dict[str, float]] = None
    time_constraints_sec: Optional[int] = None

@router.post("/admin/exam-config/update-marking-scheme")
async def update_marking_scheme(req: MarkingSchemeUpdateRequest):
    config_opt = EXAM_CONFIGS.get(req.exam_code)
    if config_opt is None:
        raise HTTPException(status_code=404, detail=f"Exam {req.exam_code} not found")
    
    # Narrow Optional to concrete type after None check
    config: ExamConfiguration = config_opt

    config.scoring_scheme = ScoringScheme(
        correct_score=req.correct_score,
        incorrect_score=req.incorrect_score,
        partial_credit_rules=req.partial_credit_rules
    )
    if req.time_constraints_sec is not None:
        config.time_constraints_sec = req.time_constraints_sec

    # TODO: persist to DB and trigger hot-reload across services
    return {"status": "success", "exam_code": req.exam_code}
