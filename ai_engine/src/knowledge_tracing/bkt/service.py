import logging
from .model import BayesianKnowledgeTracing
from .schemas import TraceRequest, TraceResponse
from .repository import BKTRepository

logger = logging.getLogger("bkt_service")
repo = BKTRepository()

async def update_knowledge_state(req: TraceRequest) -> TraceResponse:
    try:
        engine = BayesianKnowledgeTracing(concept_id=req.concept_id, repo=repo)
        result = await engine.update(
            student_id=req.student_id,
            correct=req.is_correct,
            response_time_ms=req.response_time_ms
        )
        return TraceResponse(**result)
    except Exception as e:
        logger.error(f"BKT update failed: {e}")
        raise
