# ai_engine/src/knowledge_tracing/routes/fairness_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
import logging

from ai_engine.src.knowledge_tracing.fairness.monitor import FairnessMonitor

router = APIRouter()
logger = logging.getLogger("fairness_route")
monitor = FairnessMonitor()

class FairnessUpdateRequest(BaseModel):
    exam_code: str = Field(default="JEE_Mains")
    subject: str = Field(default="generic")
    group: str
    mastery_scores: List[float]

class FairnessReportRequest(BaseModel):
    exam_code: str = Field(default="JEE_Mains")
    subject: str = Field(default="generic")

@router.post("/ai/trace/fairness/update")
async def fairness_update(req: FairnessUpdateRequest):
    try:
        monitor.update_stats(req.exam_code, req.subject, req.group, req.mastery_scores)
        return {"status": "updated", "exam_code": req.exam_code, "subject": req.subject}
    except Exception as e:
        logger.exception("Fairness update failed")
        raise HTTPException(status_code=500, detail="Update failed")

@router.post("/ai/trace/fairness/report")
async def fairness_report(req: FairnessReportRequest):
    try:
        report = monitor.check_parity(req.exam_code, req.subject)
        recs = monitor.generate_recommendations(report.get("disparity", 0.0))
        return {"exam_code": req.exam_code, "subject": req.subject, **report, "recommendations": recs}
    except Exception as e:
        logger.exception("Fairness report failed")
        raise HTTPException(status_code=500, detail="Report generation failed")
