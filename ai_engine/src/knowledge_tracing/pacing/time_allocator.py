# ai_engine/src/knowledge_tracing/pacing/time_allocator.py
from __future__ import annotations
import os
import logging
from typing import Dict
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger("time_allocator")

class TimeAllocationRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    base_time_ms: int = Field(..., gt=0)
    stress_level: float = Field(..., ge=0.0, le=1.0)
    fatigue_level: float = Field(..., ge=0.0, le=1.0)
    mastery: float = Field(..., ge=0.0, le=1.0)
    difficulty: float = Field(..., ge=0.0)
    session_elapsed_ms: int = Field(..., ge=0)

class TimeAllocationResponse(BaseModel):
    student_id: str
    question_id: str
    final_time_ms: int
    factor: float
    breakdown: Dict[str, float]
    timestamp: datetime

class DynamicTimeAllocator:
    """
    Allocates dynamic interaction time per item based on multiple factors,
    with configurable min/max bounds.
    """

    MIN_FACTOR = float(os.getenv("KT_MIN_TIME_FACTOR", "0.5"))
    MAX_FACTOR = float(os.getenv("KT_MAX_TIME_FACTOR", "2.0"))

    def allocate(self, req: TimeAllocationRequest) -> TimeAllocationResponse:
        try:
            stress_factor = 1.0 + req.stress_level * 0.5
            fatigue_factor = 1.0 + req.fatigue_level * 0.3
            mastery_factor = 1.0 - req.mastery * 0.3
            difficulty_factor = max(0.5, req.difficulty)
            session_hours = req.session_elapsed_ms / 3_600_000  # ms to hours
            session_factor = 1.0 + min(0.2, session_hours * 0.1)

            raw_factor = stress_factor * fatigue_factor * mastery_factor * difficulty_factor * session_factor
            clamped_factor = max(self.MIN_FACTOR, min(self.MAX_FACTOR, raw_factor))
            final_time = int(req.base_time_ms * clamped_factor)

            breakdown = {
                "stress_factor": stress_factor,
                "fatigue_factor": fatigue_factor,
                "mastery_factor": mastery_factor,
                "difficulty_factor": difficulty_factor,
                "session_factor": session_factor,
                "clamped_factor": clamped_factor
            }

            logger.debug(f"[TimeAllocator] raw_factor={raw_factor:.4f}, clamped={clamped_factor:.4f}, final_time={final_time}ms")

            return TimeAllocationResponse(
                student_id=req.student_id,
                question_id=req.question_id,
                final_time_ms=final_time,
                factor=round(clamped_factor, 4),
                breakdown={k: round(v, 4) for k, v in breakdown.items()},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Time allocation error: {e}", exc_info=True)
            return TimeAllocationResponse(
                student_id=req.student_id,
                question_id=req.question_id,
                final_time_ms=req.base_time_ms,
                factor=1.0,
                breakdown={"error": str(e)},
                timestamp=datetime.utcnow()
            )
