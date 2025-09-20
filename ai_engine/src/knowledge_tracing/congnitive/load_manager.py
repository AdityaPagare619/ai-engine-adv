# ai_engine/src/knowledge_tracing/cognitive/load_manager.py
from __future__ import annotations
from typing import List
from dataclasses import dataclass
import math
import logging

logger = logging.getLogger("cognitive_load")

@dataclass
class LoadAssessment:
    intrinsic_load: float
    extraneous_load: float
    germane_load: float
    total_load: float
    working_memory_capacity: float
    overload_risk: float
    recommendations: List[str]
    components: dict = None

class CognitiveLoadManager:
    """
    Implements Sweller's Cognitive Load Theory (CLT) with detailed intrinsic,
    extraneous, and germane load estimations, fatigue and stress perturbations,
    and risk scoring.
    """

    BASE_CAPACITY = 7.0  # Miller's magic 7±2 working memory units
    STRESS_IMPACT = 0.4
    FATIGUE_IMPACT = 0.3

    def assess(self,
               problem_steps: int,
               concept_mastery: float,
               prerequisites_gap: float,
               time_pressure: float,
               interface_score: float,
               distractions: float,
               stress_level: float,
               fatigue_level: float) -> LoadAssessment:
        """
        Assess cognitive load components and overall overload risk.
        """

        # Adjusted working memory capacity based on stress and fatigue
        capacity = self.BASE_CAPACITY * (1 - stress_level * self.STRESS_IMPACT - fatigue_level * self.FATIGUE_IMPACT)
        capacity = max(2.0, capacity)  # enforce minimal operational capacity

        # Intrinsic load computation components
        step_complexity = min(5.0, math.log2(problem_steps + 1))
        novelty_load = (1.0 - concept_mastery) * 3.0
        prereq_load = max(0.0, prerequisites_gap - 0.8) * 2.0
        intrinsic = 0.4 * step_complexity + 0.3 * novelty_load + 0.3 * prereq_load

        # Extraneous load computation components
        pressure_load = max(0.0, (1.0 - time_pressure)) * 4.0
        interface_load = interface_score * 3.0
        distraction_load = distractions * 2.0
        extraneous = 0.35 * pressure_load + 0.25 * interface_load + 0.25 * distraction_load

        # Germane load encourages deep processing and schema construction
        germane = max(0.0, intrinsic * 0.2)

        # Total load sum
        total = intrinsic + extraneous + germane

        # Sigmoid overload risk - nonlinear scale centered at capacity
        overload_risk = 1.0 / (1.0 + math.exp(-3.0 * (total / capacity - 1.0)))

        # Generate intervention recommendations
        recs = []
        if overload_risk > 0.7:
            recs.append("Immediate break recommended")
        if extraneous > 3.0:
            recs.append("Interface simplification suggested")
        if intrinsic > 5.0:
            recs.append("Segment problem into smaller steps")
        if germane < 1.0:
            recs.append("Increase schema activation prompts")

        logger.debug(f"[LoadAssessment] Intrinsic: {intrinsic:.3f}, Extraneous: {extraneous:.3f}, Germane: {germane:.3f}, "
                     f"Total: {total:.3f}, Capacity: {capacity:.3f}, Overload risk: {overload_risk:.3f}")

        components = {
            'step_complexity': round(step_complexity, 3),
            'novelty_load': round(novelty_load, 3),
            'prereq_load': round(prereq_load, 3),
            'pressure_load': round(pressure_load, 3),
            'interface_load': round(interface_load, 3),
            'distraction_load': round(distraction_load, 3)
        }
        
        return LoadAssessment(
            intrinsic_load=round(intrinsic, 3),
            extraneous_load=round(extraneous, 3),
            germane_load=round(germane, 3),
            total_load=round(total, 3),
            working_memory_capacity=round(capacity, 3),
            overload_risk=round(overload_risk, 3),
            recommendations=recs,
            components=components
        )
