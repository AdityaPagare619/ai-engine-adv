# ai_engine/src/knowledge_tracing/cognitive/load_manager.py
from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger("cognitive_load")

class LoadType(Enum):
    INTRINSIC = "intrinsic"
    EXTRANEOUS = "extraneous"
    GERMANE = "germane"

@dataclass
class LoadAssessment:
    """Cognitive load breakdown following Sweller's CLT framework"""
    intrinsic_load: float
    extraneous_load: float
    germane_load: float
    total_load: float
    working_memory_capacity: float
    overload_risk: float
    recommendations: List[str]

class CognitiveLoadManager:
    """
    Production-grade cognitive load assessment with desktop/mobile heuristics,
    stress/fatigue perturbations, and exam-aware knobs (via context_factors),
    preserving Phase 4A precision while fixing Phase 4B integration gaps.
    """
    BASE_CAPACITY = 7.0           # Miller's 7±2
    STRESS_REDUCTION = 0.4        # Capacity reduction per unit stress
    FATIGUE_REDUCTION = 0.3       # Capacity reduction per unit fatigue proxy

    def __init__(self):
        # Weights aligned with existing implementation; kept explicit for review
        self.complexity_weights = {
            "problem_steps": 0.40,
            "concept_novelty": 0.30,
            "prerequisite_gaps": 0.30,
        }
        self.extraneous_weights = {
            "time_pressure": 0.35,
            "interface_complexity": 0.25,
            "distraction_level": 0.25,
            "presentation_quality": 0.15,
        }

        # Mobile-aware multipliers; applied to extraneous channels when device_profile["type"] == "mobile"
        self.mobile_extraneous_multipliers = {
            "time_pressure": 1.10,         # mobile latency and jitter under poor networks
            "interface_complexity": 1.15,  # smaller screens, touch targets, zoom/pan friction
            "distraction_level": 1.20,     # more notifications/environmental interruptions
            "presentation_quality": 1.10,  # scaling/zoom artifacts, font rendering issues
        }

    def assess_cognitive_load(
        self,
        item_metadata: Dict,
        student_state: Dict,
        context_factors: Dict,
        stress_level: float = 0.0,
        device_profile: Optional[Dict] = None,
    ) -> LoadAssessment:
        """
        Compute CLT components with exam/device-aware modifiers and actionable recommendations.
        - item_metadata: {solution_steps, concepts_required[], prerequisites[], learning_value, schema_complexity}
        - student_state: {session_duration_minutes, cognitive_capacity_modifier, flow_state_factor,
                          mastery_<concept>: 0..1}
        - context_factors: {time_pressure_ratio, interface_complexity_score, distraction_level,
                            presentation_quality, exam_code?, network_quality?}
        - device_profile: {type: "mobile"|"desktop", screen_class: "small"|"medium"|"large",
                           bandwidth: "low"|"medium"|"high"}
        """
        device_profile = device_profile or {"type": "desktop", "screen_class": "large", "bandwidth": "high"}

        available_capacity = self._calculate_available_capacity(stress_level, student_state)
        intrinsic_load = self._assess_intrinsic_load(item_metadata, student_state)
        extraneous_load = self._assess_extraneous_load(context_factors, stress_level, device_profile)
        germane_load = self._assess_germane_load(item_metadata, student_state, intrinsic_load)

        total_load = intrinsic_load + extraneous_load + germane_load
        overload_risk = self._calculate_overload_risk(total_load, available_capacity)
        recommendations = self._generate_recommendations(
            intrinsic_load, extraneous_load, germane_load, available_capacity, overload_risk, device_profile
        )

        logger.debug(
            f"[Load] intrinsic={intrinsic_load:.3f} extraneous={extraneous_load:.3f} "
            f"germane={germane_load:.3f} total={total_load:.3f} "
            f"capacity={available_capacity:.3f} overload={overload_risk:.3f} device={device_profile}"
        )

        return LoadAssessment(
            intrinsic_load=round(intrinsic_load, 3),
            extraneous_load=round(extraneous_load, 3),
            germane_load=round(germane_load, 3),
            total_load=round(total_load, 3),
            working_memory_capacity=round(available_capacity, 3),
            overload_risk=round(overload_risk, 3),
            recommendations=recommendations,
        )

    # -----------------------
    # Internal calculation methods
    # -----------------------
    def _calculate_available_capacity(self, stress_level: float, student_state: Dict) -> float:
        base_capacity = self.BASE_CAPACITY
        stress_reduction = stress_level * self.STRESS_REDUCTION
        session_minutes = float(student_state.get("session_duration_minutes", 0.0))
        session_hours = max(0.0, session_minutes) / 60.0
        fatigue_factor = min(1.0, session_hours / 2.0)  # saturates after ~2h continuous session
        fatigue_reduction = fatigue_factor * self.FATIGUE_REDUCTION
        individual_modifier = float(student_state.get("cognitive_capacity_modifier", 1.0))
        capacity = base_capacity * individual_modifier * (1 - stress_reduction - fatigue_reduction)
        return max(2.0, capacity)

    def _assess_intrinsic_load(self, item_metadata: Dict, student_state: Dict) -> float:
        steps = int(item_metadata.get("solution_steps", 1))
        step_load = min(5.0, math.log2(max(1, steps) + 1))

        required_concepts = item_metadata.get("concepts_required", [])
        mastery_scores = [float(student_state.get(f"mastery_{c}", 0.0)) for c in required_concepts]
        avg_mastery = (sum(mastery_scores) / max(len(mastery_scores), 1)) if required_concepts else 0.0
        novelty_load = (1.0 - max(0.0, min(1.0, avg_mastery))) * 3.0

        prereqs = item_metadata.get("prerequisites", [])
        prereq_scores = [float(student_state.get(f"mastery_{c}", 0.0)) for c in prereqs]
        avg_prereq_mastery = (sum(prereq_scores) / max(len(prereq_scores), 1)) if prereqs else 0.0
        prereq_load = max(0.0, 0.8 - avg_prereq_mastery) * 2.0

        return (
            self.complexity_weights["problem_steps"] * step_load
            + self.complexity_weights["concept_novelty"] * novelty_load
            + self.complexity_weights["prerequisite_gaps"] * prereq_load
        )

    def _assess_extraneous_load(self, context_factors: Dict, stress_level: float, device_profile: Dict) -> float:
        time_ratio = float(context_factors.get("time_pressure_ratio", 1.0))
        pressure_load = max(0.0, (1.0 - time_ratio)) * 4.0

        interface_score = float(context_factors.get("interface_complexity_score", 0.0))
        distraction_score = float(context_factors.get("distraction_level", 0.0))
        presentation_quality = float(context_factors.get("presentation_quality", 1.0))
        presentation_load = (1.0 - max(0.0, min(1.0, presentation_quality))) * 2.0

        stress_load = max(0.0, min(1.0, stress_level)) * 1.5

        # Device-aware multipliers
        multipliers = self.mobile_extraneous_multipliers if device_profile.get("type") == "mobile" else {
            "time_pressure": 1.0, "interface_complexity": 1.0, "distraction_level": 1.0, "presentation_quality": 1.0
        }

        extraneous = (
            self.extraneous_weights["time_pressure"] * pressure_load * multipliers["time_pressure"]
            + self.extraneous_weights["interface_complexity"] * interface_score * 3.0 * multipliers["interface_complexity"]
            + self.extraneous_weights["distraction_level"] * distraction_score * 2.0 * multipliers["distraction_level"]
            + self.extraneous_weights["presentation_quality"] * presentation_load * multipliers["presentation_quality"]
            + stress_load
        )
        return extraneous

    def _assess_germane_load(self, item_metadata: Dict, student_state: Dict, intrinsic_load: float) -> float:
        learning_value = float(item_metadata.get("learning_value", 0.5))
        schema_demand = float(item_metadata.get("schema_complexity", 0.3))
        flow_bonus = float(student_state.get("flow_state_factor", 1.0))
        base_germane = learning_value * 2.0 + schema_demand * 1.5
        capacity_available = max(0.0, 1.0 - (intrinsic_load / 6.0))  # 6≈soft cap for intrinsic
        return base_germane * capacity_available * flow_bonus

    def _calculate_overload_risk(self, total_load: float, available_capacity: float) -> float:
        ratio = (total_load / max(1e-6, available_capacity))
        return 1.0 / (1.0 + math.exp(-3.0 * (ratio - 1.0)))

    def _generate_recommendations(
        self,
        intrinsic_load: float,
        extraneous_load: float,
        germane_load: float,
        capacity: float,
        overload_risk: float,
        device_profile: Dict,
    ) -> List[str]:
        recs: List[str] = []
        if overload_risk > 0.7:
            recs.append("URGENT: Cognitive overload detected - recommend immediate break")
        if extraneous_load > 3.0:
            if device_profile.get("type") == "mobile":
                recs.append("Reduce time pressure and notifications; enable do-not-disturb during test")
                recs.append("Simplify UI for touch; enlarge targets and reduce clutter")
            else:
                recs.append("Reduce time pressure and distractions")
                recs.append("Simplify interface - remove non-essential elements")
        if intrinsic_load > 5.0:
            recs.append("Split complex problem into smaller steps")
            recs.append("Provide prerequisite review")
        if germane_load < 1.0 and intrinsic_load < 4.0:
            recs.append("Encourage reflection and schema-building prompts")
        if capacity < 4.0:
            recs.append("Address stress/fatigue - suggest relaxation or short break")
        return recs
