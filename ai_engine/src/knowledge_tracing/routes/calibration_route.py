# ai_engine/src/knowledge_tracing/routes/calibration_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import torch
import logging

from ..calibration.calibrator import TemperatureScalingCalibrator

router = APIRouter()
logger = logging.getLogger("calibration_route")

class CalibrationFitRequest(BaseModel):
    logits: List[List[float]]  # Raw logits matrix (N x C)
    labels: List[int]          # True labels (N)

class CalibrationCalibrateRequest(BaseModel):
    logits: List[List[float]]  # Raw logits matrix (N x C)

@router.post("/ai/trace/calibration/fit")
async def fit_temperature(request: CalibrationFitRequest):
    try:
        logits = torch.tensor(request.logits, dtype=torch.float32)
        labels = torch.tensor(request.labels, dtype=torch.long)
        calibrator = TemperatureScalingCalibrator()
        calibrator.fit(logits, labels)
        return {"temperature": float(calibrator.temperature.item())}
    except Exception as e:
        logger.error(f"Calibration fit error: {e}")
        raise HTTPException(status_code=500, detail="Calibration fit failed")

@router.post("/ai/trace/calibration/calibrate")
async def calibrate_logits(request: CalibrationCalibrateRequest):
    try:
        logits = torch.tensor(request.logits, dtype=torch.float32)
        calibrator = TemperatureScalingCalibrator()
        # In real scenario, calibrator should be a shared instance fitted beforehand
        probs = calibrator.calibrate(logits)
        return {"probabilities": probs.tolist()}
    except Exception as e:
        logger.error(f"Calibration error: {e}")
        raise HTTPException(status_code=500, detail="Calibration error")
