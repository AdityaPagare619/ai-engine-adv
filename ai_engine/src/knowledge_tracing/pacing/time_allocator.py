# ai_engine/src/knowledge_tracing/pacing/time_allocator.py
from __future__ import annotations
import os
import logging
from typing import Dict
from datetime import datetime
from pydantic import BaseModel, Field

from ai_engine.src.config.exam_config import EXAM_CONFIGS

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
    exam_code: str = Field(default="JEE_Mains")

class TimeAllocationResponse(BaseModel):
    student_id: str
    question_id: str
    final_time_ms: int
    factor: float
    breakdown: Dict[str, float]
    timestamp: datetime

class DynamicTimeAllocator:
    MIN_FACTOR = float(os.getenv("KT_MIN_TIME_FACTOR", "0.5"))
    MAX_FACTOR = float(os.getenv("KT_MAX_TIME_FACTOR", "2.0"))

    def allocate(self, req: TimeAllocationRequest, mobile_headers=None) -> TimeAllocationResponse:
        try:
            config = EXAM_CONFIGS.get(req.exam_code) or EXAM_CONFIGS["JEE_Mains"]

            # Apply exam-specific difficulty scaling
            exam_difficulty_factor = 1.0
            if req.exam_code == "JEE_Advanced":
                exam_difficulty_factor = 1.4  # JEE Advanced is more challenging
            elif req.exam_code == "NEET":
                exam_difficulty_factor = 0.9  # NEET has different time requirements

            stress_factor = 1.0 + req.stress_level * 0.5
            fatigue_factor = 1.0 + req.fatigue_level * 0.3
            mastery_factor = 1.0 - req.mastery * 0.3
            difficulty_factor = max(0.5, req.difficulty) * exam_difficulty_factor
            session_hours = req.session_elapsed_ms / 3_600_000
            session_factor = 1.0 + min(0.2, session_hours * 0.1)
            
            # Process mobile headers if present
            mobile_factor = 1.0
            if mobile_headers and mobile_headers.get("device_type") == "mobile":
                # Add mobile-specific factors
                if mobile_headers.get("screen_class") == "small":
                    mobile_factor *= 1.2  # Small screens need more time
                
                # Network quality impacts time
                network = mobile_headers.get("network", "high")
                if network == "low":
                    mobile_factor *= 1.3
                elif network == "medium":
                    mobile_factor *= 1.15
                
                # Distraction level impacts time
                if mobile_headers.get("distraction_level"):
                    try:
                        distraction = float(mobile_headers.get("distraction_level", "0"))
                        mobile_factor *= (1.0 + distraction * 0.2)
                    except ValueError:
                        pass

            raw_factor = stress_factor * fatigue_factor * mastery_factor * difficulty_factor * session_factor * mobile_factor
            clamped_factor = max(self.MIN_FACTOR, min(self.MAX_FACTOR, raw_factor))

            base_time = req.base_time_ms
            max_allowed = config.time_constraints_sec * 1000
            final_time = min(int(base_time * clamped_factor), max_allowed)

            breakdown = {
                "stress_factor": stress_factor,
                "fatigue_factor": fatigue_factor,
                "mastery_factor": mastery_factor,
                "difficulty_factor": difficulty_factor,
                "exam_difficulty_factor": exam_difficulty_factor,
                "session_factor": session_factor,
                "clamped_factor": clamped_factor,
                "max_allowed_time_ms": float(max_allowed)
            }
            
            # Add mobile factor to breakdown if present
            if mobile_headers and mobile_headers.get("device_type") == "mobile":
                breakdown["mobile_factor"] = mobile_factor

            logger.debug(f"[TimeAllocator] raw={raw_factor:.4f}, clamp={clamped_factor:.4f}, final={final_time}ms exam={req.exam_code}")
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
                breakdown={"error": float(str(e).replace("'", ""))},
                timestamp=datetime.utcnow()
            )
