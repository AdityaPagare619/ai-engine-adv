# ai_engine/src/knowledge_tracing/middleware/context_injector.py
from __future__ import annotations
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from ai_engine.src.knowledge_tracing.stress.detection_engine import MultiModalStressDetector
from ai_engine.src.knowledge_tracing.cognitive.load_manager import CognitiveLoadManager

logger = logging.getLogger("context_injector")

class ContextInjectorMiddleware(BaseHTTPMiddleware):
    """
    Derives exam_code and device_profile from headers, computes stress and cognitive load,
    and injects them into request.state for downstream usage across pacing/BKT/selection.
    """
    def __init__(self, app, window_size: int = 12):
        super().__init__(app)
        self.stress_detector = MultiModalStressDetector(window_size=window_size)
        self.load_manager = CognitiveLoadManager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Core exam context
            exam_code = request.headers.get("X-Exam-Code") or "JEE_Mains"

            # Behavioral signals
            rt = float(request.headers.get("X-Response-Time", "0") or "0")
            correct = request.headers.get("X-Is-Correct", "false").lower() == "true"
            hesitation_ms = float(request.headers.get("X-Hesitation", "0") or "0")
            keystroke_dev = float(request.headers.get("X-Keystroke-Dev", "0") or "0")

            # Device and network
            device_type = (request.headers.get("X-Device-Type") or "desktop").lower()
            screen_class = (request.headers.get("X-Screen-Class") or "large").lower()
            bandwidth = (request.headers.get("X-Network", "high") or "high").lower()
            device_profile = {"type": device_type, "screen_class": screen_class, "bandwidth": bandwidth}

            # Stress detection
            stress_res = self.stress_detector.detect(rt, correct, hesitation_ms=hesitation_ms, keystroke_dev=keystroke_dev)
            stress_level = float(stress_res.level)

            # Cognitive load inputs
            item_metadata = {
                "solution_steps": int(request.headers.get("X-Item-Steps", "1") or "1"),
                "concepts_required": (request.headers.get("X-Concepts-Required", "")).split(",") if request.headers.get("X-Concepts-Required") else [],
                "prerequisites": (request.headers.get("X-Prerequisites", "")).split(",") if request.headers.get("X-Prerequisites") else [],
                "learning_value": float(request.headers.get("X-Learning-Value", "0.5") or "0.5"),
                "schema_complexity": float(request.headers.get("X-Schema-Complexity", "0.3") or "0.3"),
            }
            student_state = {
                "session_duration_minutes": float(request.headers.get("X-Session-Minutes", "0") or "0"),
                "cognitive_capacity_modifier": float(request.headers.get("X-Capacity-Modifier", "1.0") or "1.0"),
                "flow_state_factor": float(request.headers.get("X-Flow-State", "1.0") or "1.0"),
            }
            context_factors = {
                "time_pressure_ratio": float(request.headers.get("X-Time-Pressure", "1.0") or "1.0"),
                "interface_complexity_score": float(request.headers.get("X-Interface-Score", "0.0") or "0.0"),
                "distraction_level": float(request.headers.get("X-Distraction-Level", "0.0") or "0.0"),
                "presentation_quality": float(request.headers.get("X-Presentation-Quality", "1.0") or "1.0"),
                "exam_code": exam_code,
                "network_quality": bandwidth,
            }

            load_assess = self.load_manager.assess_cognitive_load(
                item_metadata=item_metadata,
                student_state=student_state,
                context_factors=context_factors,
                stress_level=stress_level,
                device_profile=device_profile,
            )

            # Export to state
            request.state.exam_code = exam_code
            request.state.stress_level = stress_level
            request.state.cognitive_load = float(load_assess.total_load)
            request.state.overload_risk = float(load_assess.overload_risk)
            request.state.device_profile = device_profile

        except Exception as e:
            logger.exception("ContextInjectorMiddleware error; defaulting to safe state")
            request.state.exam_code = "JEE_Mains"
            request.state.stress_level = 0.0
            request.state.cognitive_load = 0.0
            request.state.overload_risk = 0.0
            request.state.device_profile = {"type": "desktop", "screen_class": "large", "bandwidth": "high"}

        response = await call_next(request)
        return response
