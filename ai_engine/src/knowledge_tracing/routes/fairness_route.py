# ai_engine/src/knowledge_tracing/routes/fairness_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging

from ..fairness.monitor import FairnessMonitor

router = APIRouter()
logger = logging.getLogger("fairness_route")

class FairnessUpdateRequest(BaseModel):
    group: str
    mastery_scores: List[float]

class FairnessReportResponse(BaseModel):
    averages: Dict[str, float]
    disparity: float
    recommendations: List[str]

monitor = FairnessMonitor()

@router.post("/ai/trace/fairness/update")
async def update_fairness(data: FairnessUpdateRequest):
    try:
        monitor.update_stats(data.group, data.mastery_scores)
        return {"status": "updated"}
    except Exception as e:
        logger.error(f"Fairness update error: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@router.get("/ai/trace/fairness/report", response_model=FairnessReportResponse)
async def get_fairness_report():
    try:
        report = monitor.check_parity()
        recommendations = monitor.generate_recommendations()
        return FairnessReportResponse(averages=report.get("averages", {}), disparity=report.get("disparity", 0.0), recommendations=recommendations)
    except Exception as e:
        logger.error(f"Fairness report error: {e}")
        raise HTTPException(status_code=500, detail="Report generation failed")
