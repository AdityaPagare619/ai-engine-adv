# ai_engine/src/knowledge_tracing/routes/selection_route.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List

from ..selection.bandit_policy import LinUCBPolicy, build_contexts_from_candidates, default_feature_map
from ..selection.candidate_provider import CandidateProvider
from ..bkt.repository import BKTRepository
from ..core.bkt_core import CanonicalBKTCore

router = APIRouter(prefix="/ai/trace", tags=["selection"])

_bandit = LinUCBPolicy(d=10, alpha=0.6)   # d must match default_feature_map dimension
_candidates = CandidateProvider()
_repo = BKTRepository()

@router.get("/select")
async def select_next_item(
    student_id: str,
    concept_id: str,
    subject: Optional[str] = None,
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Select next question via LinUCB over candidate metadata with interpretable features.
    """
    try:
        # Load student state for mastery/confidence proxy
        state = _repo.get_state(student_id, concept_id)
        mastery = float(state.mastery_probability)
        # Confidence proxy: 1 - uncertainty (here, naive function of practice count)
        confidence = float(min(0.95, 0.5 + 0.05 * max(state.practice_count, 0)))

        # Fetch candidates and build bandit contexts
        cand = _candidates.build_bandit_inputs(
            student_id=student_id, concept_id=concept_id, subject=subject, topic=topic, limit=100
        )
        if not cand:
            raise HTTPException(status_code=404, detail="No candidates found for selection.")

        contexts = build_contexts_from_candidates(
            student_id=student_id, concept_id=concept_id, candidates=cand, mastery=mastery, confidence=confidence
        )

        # Score and choose
        best_id, details = _bandit.select(contexts)
        # Return chosen item with human-readable debug info
        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "chosen_question_id": best_id,
            "debug": details,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection failed: {e}")
