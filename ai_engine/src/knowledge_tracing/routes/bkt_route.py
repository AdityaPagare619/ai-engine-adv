# ai_engine/src/knowledge_tracing/routes/bkt_route.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..bkt.schemas import TraceRequest, TraceResponse, EvaluateWindowRequest, EvaluateWindowResponse
from ..service.advanced_bkt_service import AdvancedBKTService
from ..evaluation.metrics import BKTEvaluationSuite

router = APIRouter(prefix="/ai/trace", tags=["knowledge-tracing"])
service = AdvancedBKTService()
evaluator = BKTEvaluationSuite()

@router.post("/update", response_model=TraceResponse)
async def update_trace(req: TraceRequest) -> TraceResponse:
    try:
        result = await service.update_mastery(
            student_id=req.student_id,
            concept_id=req.concept_id,
            is_correct=req.is_correct,
            question_id=req.question_id,
            response_time_ms=req.response_time_ms,
        )
        return TraceResponse(
            previous_mastery=result.previous_mastery,
            posterior_mastery=result.posterior_mastery,
            new_mastery=result.new_mastery,
            p_correct_pred=result.p_correct_pred,
            adjusted_params={
                "learn_rate": float(result.adjusted_params.learn_rate),
                "slip_rate": float(result.adjusted_params.slip_rate),
                "guess_rate": float(result.adjusted_params.guess_rate),
            },
            constraint_violations=result.constraint_violations,
            explanation=result.explanation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BKT update failed: {e}")

@router.post("/evaluate", response_model=EvaluateWindowResponse)
async def evaluate_trace(req: EvaluateWindowRequest) -> EvaluateWindowResponse:
    try:
        # In a real system, fetch interactions within window and optional concept filter.
        # Here, evaluator expects data records with fields: y_true, y_pred_prob, mastery_seq per student-concept.
        report = evaluator.evaluate_window(concept_id=req.concept_id, start_ts=req.start_ts, end_ts=req.end_ts)
        return EvaluateWindowResponse(
            next_step_auc=report["next_step_auc"],
            next_step_accuracy=report["next_step_accuracy"],
            brier_score=report["brier_score"],
            calibration_error=report["calibration_error"],
            trajectory_validity=report["trajectory_validity"],
            recommendation=report["recommendation"],
            details=report.get("details", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
