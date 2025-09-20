# ai_engine/src/knowledge_tracing/middleware/context_injector.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from ..stress.detection_engine import MultiModalStressDetector
from ..cognitive.load_manager import CognitiveLoadManager

logger = logging.getLogger("context_injector")

class ContextInjectorMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting stress_level and cognitive_load into request.state
    for downstream routes and policies.
    """

    def __init__(self, app, window_size: int = 12):
        super().__init__(app)
        self.stress_detector = MultiModalStressDetector(window_size=window_size)
        self.load_manager = CognitiveLoadManager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Extract behavioral headers
            rt = float(request.headers.get("X-Response-Time", 0.0))
            correct = request.headers.get("X-Is-Correct", "false").lower() == "true"
            hes = float(request.headers.get("X-Hesitation", 0.0))
            key_dev = float(request.headers.get("X-Keystroke-Dev", 0.0))

            # Detect stress level
            stress_res = self.stress_detector.detect(rt, correct, hesitation_ms=hes, keystroke_dev=key_dev)
            stress_level = stress_res.level

            # Extract cognitive load parameters
            steps = int(request.headers.get("X-Item-Steps", 1))
            mastery = float(request.headers.get("X-Mastery-Level", 0.0))
            prereq_gap = float(request.headers.get("X-Prereq-Gap", 0.0))
            time_pressure = float(request.headers.get("X-Time-Pressure", 1.0))
            interface_score = float(request.headers.get("X-Interface-Score", 1.0))
            distractions = float(request.headers.get("X-Distraction-Level", 0.0))

            fatigue_level = float(request.headers.get("X-Fatigue-Level", 0.0))

            load_res = self.load_manager.assess(
                problem_steps=steps,
                concept_mastery=mastery,
                prerequisites_gap=prereq_gap,
                time_pressure=time_pressure,
                interface_score=interface_score,
                distractions=distractions,
                stress_level=stress_level,
                fatigue_level=fatigue_level
            )

            # Inject into state
            request.state.stress_level = stress_level
            request.state.cognitive_load = load_res.total_load

        except Exception as e:
            logger.exception("Context injection error; defaulting to zero")
            request.state.stress_level = 0.0
            request.state.cognitive_load = 0.0

        response = await call_next(request)
        return response
