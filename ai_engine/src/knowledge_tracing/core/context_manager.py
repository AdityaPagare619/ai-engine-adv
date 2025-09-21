# ai_engine/src/core/context_manager.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai_engine.src.config.exam_config import EXAM_CONFIGS
from ai_engine.src.knowledge_tracing.stress.detection_engine import MultiModalStressDetector
from ai_engine.src.knowledge_tracing.cognitive.load_manager import CognitiveLoadManager
from ai_engine.src.knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
from ai_engine.src.knowledge_tracing.bkt.bkt_engine import BKTEngine
from ai_engine.src.knowledge_tracing.fairness.monitor import FairnessMonitor
from ai_engine.src.knowledge_tracing.spaced_repetition.scheduler import HalfLifeRegressionScheduler
from ai_engine.src.knowledge_tracing.selection.candidate_provider import CandidateProvider
from ai_engine.src.knowledge_tracing.selection.bandit_policy import BanditContext
from ai_engine.src.knowledge_tracing.selection.pressure_linucb import PressureAwareLinUCB

@dataclass
class StudentInteraction:
    student_id: str
    question_id: str
    subject: Optional[str]
    topic: Optional[str]
    response_time_ms: float
    hesitation_ms: float
    keystroke_dev: float
    correct: bool
    mastery: float
    difficulty: float
    session_elapsed_ms: int
    exam_code: str
    problem_steps: int
    concepts_required: List[str]
    prerequisites: List[str]
    learning_value: float
    schema_complexity: float
    time_pressure_ratio: float
    interface_complexity_score: float
    distraction_level: float
    presentation_quality: float
    fatigue_minutes: float
    device_profile: Dict

@dataclass
class IntegratedDecision:
    stress: Dict[str, Any]
    load: Dict[str, Any]
    time: Dict[str, Any]
    mastery: Dict[str, Any]
    fairness: Dict[str, Any]
    schedule: Dict[str, Any]
    selection: Dict[str, Any]

class CentralContextManager:
    def __init__(self, exam_code: str = "JEE_Mains"):
        self.exam_code = exam_code
        self.config = EXAM_CONFIGS.get(exam_code, EXAM_CONFIGS["JEE_Mains"])
        self.stress_detector = MultiModalStressDetector(window_size=12)
        self.load_manager = CognitiveLoadManager()
        self.time_allocator = DynamicTimeAllocator()
        self.bkt_engine = BKTEngine(exam_code=exam_code)
        self.fairness_monitor = FairnessMonitor()
        self.scheduler = HalfLifeRegressionScheduler()
        self.candidate_provider = CandidateProvider(datasource=None, exam_code=exam_code)
        self.bandit = PressureAwareLinUCB(alpha=0.6)

    def process(self, x: StudentInteraction) -> IntegratedDecision:
        # 1) Stress
        stress_res = self.stress_detector.detect(
            response_time=x.response_time_ms, correct=x.correct,
            hesitation_ms=x.hesitation_ms, keystroke_dev=x.keystroke_dev
        )
        stress_payload = {
            "level": float(stress_res.level),
            "confidence": float(stress_res.confidence),
            "indicators": stress_res.indicators,
            "intervention": stress_res.intervention,
        }

        # 2) Cognitive Load (match assess_cognitive_load API)
        item_metadata = {
            "solution_steps": x.problem_steps,
            "concepts_required": x.concepts_required,
            "prerequisites": x.prerequisites,
            "learning_value": x.learning_value,
            "schema_complexity": x.schema_complexity,
        }
        student_state = {
            "session_duration_minutes": x.fatigue_minutes,
            "cognitive_capacity_modifier": 1.0,
            "flow_state_factor": 1.0,
            **{f"mastery_{c}": x.mastery for c in set(x.concepts_required + x.prerequisites)}
        }
        context_factors = {
            "time_pressure_ratio": x.time_pressure_ratio,
            "interface_complexity_score": x.interface_complexity_score,
            "distraction_level": x.distraction_level,
            "presentation_quality": x.presentation_quality,
            "exam_code": x.exam_code,
            "network_quality": x.device_profile.get("bandwidth", "high"),
        }
        load_assess = self.load_manager.assess_cognitive_load(
            item_metadata=item_metadata,
            student_state=student_state,
            context_factors=context_factors,
            stress_level=stress_payload["level"],
            device_profile=x.device_profile,
        )
        load_payload = {
            "intrinsic": load_assess.intrinsic_load,
            "extraneous": load_assess.extraneous_load,
            "germane": load_assess.germane_load,
            "total": load_assess.total_load,
            "capacity": load_assess.working_memory_capacity,
            "overload_risk": load_assess.overload_risk,
            "recommendations": load_assess.recommendations,
        }

        # 3) Time Allocation
        time_req = TimeAllocationRequest(
            student_id=x.student_id,
            question_id=x.question_id,
            base_time_ms=max(10000, int(x.response_time_ms) or 30000),
            stress_level=stress_payload["level"],
            fatigue_level=min(1.0, x.fatigue_minutes / 120.0),  # map ~0-120min to 0-1
            mastery=x.mastery,
            difficulty=x.difficulty,
            session_elapsed_ms=int(x.session_elapsed_ms),
            exam_code=x.exam_code,
        )
        time_alloc = self.time_allocator.allocate(time_req)
        time_payload = time_alloc.dict()

        # 4) BKT Update
        bkt = self.bkt_engine.update(
            student_response={
                "student_id": x.student_id,
                "question_id": x.question_id,
                "correct": x.correct,
                "difficulty": x.difficulty,
                "subject": x.subject,
                "topic": x.topic,
                "response_time_ms": x.response_time_ms,
            },
            stress_level=stress_payload["level"],
            cognitive_load=load_payload["total"],
            time_pressure_factor=min(2.0, max(0.5, time_payload.get("factor", 1.0))),
        )
        mastery_payload = {"mastery": float(bkt.get("mastery", x.mastery))}

        # 5) Fairness (segmented externally; placeholder)
        fairness_report = self.fairness_monitor.check_parity()
        fairness_payload = {
            "averages": fairness_report.get("averages", {}),
            "disparity": fairness_report.get("disparity", 0.0),
            "recommendations": self.fairness_monitor.generate_recommendations(),
        }

        # 6) Spaced Repetition
        half_life_hours = self.scheduler.estimate_half_life(
            difficulty=x.difficulty,
            ability=mastery_payload["mastery"],
            features={"stress": stress_payload["level"], "load": load_payload["total"]},
        )
        schedule_payload = {"half_life_hours": float(half_life_hours)}

        # 7) Selection (exam-aware payoff)
        candidates = self.candidate_provider.build_candidates(
            student_id=x.student_id,
            concept_id=x.topic or "",
            subject=x.subject,
            topic=x.topic,
            limit=50,
            stress_level=stress_payload["level"],
            cognitive_load=load_payload["total"],
        )
        contexts: List[BanditContext] = [BanditContext(arm_id=c["arm_id"], features=c["features"]) for c in candidates]
        chosen_arm, diagnostics = self.bandit.select_with_pressure(contexts)
        selection_payload = {"arm_id": chosen_arm, "ucb_scores": diagnostics}

        return IntegratedDecision(
            stress=stress_payload,
            load=load_payload,
            time=time_payload,
            mastery=mastery_payload,
            fairness=fairness_payload,
            schedule=schedule_payload,
            selection=selection_payload,
        )
