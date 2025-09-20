# ai_engine/src/knowledge_tracing/routes/spaced_repetition_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import logging

from ..spaced_repetition.scheduler import HalfLifeRegressionScheduler

router = APIRouter()
logger = logging.getLogger("spaced_repetition_route")

class ReviewIntervalRequest(BaseModel):
    difficulty: float = Field(..., ge=0.0, le=1.0)
    ability: float = Field(..., ge=0.0, le=1.0)
    last_review: datetime

class ReviewIntervalResponse(BaseModel):
    next_review: datetime

scheduler = HalfLifeRegressionScheduler()

@router.post("/ai/trace/spaced_repetition/next_review", response_model=ReviewIntervalResponse)
async def get_next_review_time(request: ReviewIntervalRequest):
    try:
        half_life_hours = scheduler.estimate_half_life(request.difficulty, request.ability, {})
        next_review = scheduler.next_review_time(request.last_review, half_life_hours)
        return ReviewIntervalResponse(next_review=next_review)
    except Exception as e:
        logger.error(f"Spaced repetition error: {e}")
        raise HTTPException(status_code=500, detail="Scheduling failed")
