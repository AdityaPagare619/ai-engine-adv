import logging
from .model import BayesianKnowledgeTracing
from .schemas import TraceRequest, TraceResponse
from .repository import BKTRepository
from .integration import BKTInterventionIntegration

logger = logging.getLogger("bkt_service")
repo = BKTRepository()
intervention_integration = BKTInterventionIntegration()

async def update_knowledge_state(req: TraceRequest) -> TraceResponse:
    try:
        engine = BayesianKnowledgeTracing(concept_id=req.concept_id, repo=repo)
        result = await engine.update(
            student_id=req.student_id,
            correct=req.is_correct,
            response_time_ms=req.response_time_ms,
            question_id=req.question_id  # Pass question ID for context
        )
        
        # Check for performance decline and get intervention if needed
        intervention = await intervention_integration.process_response(
            student_id=req.student_id,
            concept_id=req.concept_id,
            is_correct=req.is_correct,
            response_time_ms=req.response_time_ms,
            bkt_model=engine,
            bkt_result=result,
            question_difficulty=req.difficulty if hasattr(req, 'difficulty') else 0.5,
            time_pressure=req.time_pressure if hasattr(req, 'time_pressure') else 0.0
        )
        
        # Include intervention data in response if available
        response_data = dict(result)
        if intervention:
            response_data["intervention"] = {
                "strategy": intervention.strategy_applied.name,
                "level": intervention.strategy_applied.level.name,
                "recommendations": intervention.recommendations,
                "success_probability": intervention.success_probability
            }
            
        return TraceResponse(**response_data)
    except Exception as e:
        logger.error(f"BKT update failed: {e}")
        raise
