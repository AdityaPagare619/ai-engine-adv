# ai_engine/src/knowledge_tracing/routes/evaluation_route.py
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from ..evaluation.run_evaluation_job import run_evaluation

router = APIRouter(prefix="/ai/trace", tags=["evaluation"])

@router.post("/evaluate_and_save")
async def evaluate_and_save(
    concept_id: Optional[str] = None,
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs the evaluation job for the given window, persists results to bkt_evaluation_windows,
    and returns the computed metrics and recommendation.
    """
    try:
        report = run_evaluation(concept_id=concept_id, start_ts=start_ts, end_ts=end_ts)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation run failed: {e}")
