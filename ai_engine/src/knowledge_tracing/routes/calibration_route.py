# ai_engine/src/knowledge_tracing/routes/calibration_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import torch
import logging

from ai_engine.src.knowledge_tracing.calibration.calibrator import CALIBRATOR_REGISTRY

router = APIRouter()
logger = logging.getLogger("calibration_route")

class CalibrationFitRequest(BaseModel):
    logits: List[List[float]]
    labels: List[int]
    exam_code: str = Field(default="JEE_Mains")
    subject: str = Field(default="generic")

class CalibrationApplyRequest(BaseModel):
    logits: List[List[float]]
    exam_code: str = Field(default="JEE_Mains")
    subject: str = Field(default="generic")

@router.post("/ai/trace/calibration/fit")
async def fit_temperature(req: CalibrationFitRequest):
    try:
        logits = torch.tensor(req.logits, dtype=torch.float32)
        labels = torch.tensor(req.labels, dtype=torch.long)
        T = CALIBRATOR_REGISTRY.fit(logits, labels, req.exam_code, req.subject)
        return {"temperature": T, "exam_code": req.exam_code, "subject": req.subject}
    except Exception as e:
        logger.exception("Calibration fit failed")
        raise HTTPException(status_code=500, detail="Calibration fit failed")

@router.post("/ai/trace/calibration/apply")
async def apply_calibration(req: CalibrationApplyRequest):
    try:
        logits = torch.tensor(req.logits, dtype=torch.float32)
        probs = CALIBRATOR_REGISTRY.calibrate(logits, req.exam_code, req.subject)
        return {"probabilities": probs.tolist(), "exam_code": req.exam_code, "subject": req.subject}
    except Exception as e:
        logger.exception("Calibration apply failed")
        raise HTTPException(status_code=500, detail="Calibration error")
