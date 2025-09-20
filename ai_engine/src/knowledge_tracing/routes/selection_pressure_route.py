# ai_engine/src/knowledge_tracing/routes/selection_pressure_route.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Any, Dict
from ..selection.pressure_linucb import PressureAwareLinUCB
from ..selection.candidate_provider import CandidateProvider
from ..bkt.repository import BKTRepository

router = APIRouter(prefix="/ai/trace", tags=["selection-pressure"])

# Initialize dependencies
_bandit = PressureAwareLinUCB(d=12, alpha=0.6)
_candidates = CandidateProvider()
_repo = BKTRepository()

@router.get("/select-pressure")
async def select_pressure(
    student_id: str,
    concept_id: str,
    subject: Optional[str] = Query(None),
    topic: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Pressure-aware selection endpoint.
    """
    try:
        state = _repo.get_state(student_id, concept_id)
        mastery = float(state.mastery_probability)
        confidence = min(0.95, 0.5 + 0.05 * state.practice_count)

        candidates = _candidates.build_candidates(
            student_id=student_id,
            concept_id=concept_id,
            subject=subject, topic=topic,
            limit=100
        )
        contexts = _bandit.build_contexts_from_candidates(
            student_id, concept_id,
            candidates, mastery, confidence
        )
        arm_id, debug = _bandit.select_with_pressure(contexts)
        return {"chosen_question_id": arm_id, "debug": debug}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection error: {e}")
