# ai_engine/src/knowledge_tracing/routes/feedback_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from ..bkt.repository_supabase import SupabaseClient

router = APIRouter(prefix="/ai/trace", tags=["feedback"])
_sb = SupabaseClient()

class SelectionFeedbackRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    concept_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    policy: str = Field(default="LinUCB")
    score: float = Field(..., ge=-1e6, le=1e6)
    reward: Optional[float] = Field(None, ge=0.0, le=1.0)  # correctness or learning gain
    features: Dict[str, Any] = Field(default_factory=dict)
    debug: Dict[str, Any] = Field(default_factory=dict)

@router.post("/feedback")
async def record_selection_feedback(req: SelectionFeedbackRequest) -> Dict[str, Any]:
    """
    Records selection feedback for contextual bandit learning and audits.
    Persists to bkt_selection_feedback (see migration 006).
    """
    try:
        payload = req.dict()
        _sb.table("bkt_selection_feedback").insert(payload).execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback logging failed: {e}")
