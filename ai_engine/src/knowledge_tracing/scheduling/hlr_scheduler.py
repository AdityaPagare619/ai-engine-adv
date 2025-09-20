# ai_engine/src/knowledge_tracing/scheduling/hlr_scheduler.py
from __future__ import annotations
import math
from typing import Dict, Any, Optional

class HalfLifeRegressionScheduler:
    """
    Half-Life Regression (HLR) inspired scheduler for spaced repetition:
      p(recall at Δt) = exp(-Δt / h), with h parameterized by features.  # Ref
    We expose a minimal interface that maps current mastery and recent correctness
    into an effective half-life and returns the optimal next review gap to hit a
    target retention probability.
    """

    def __init__(self):
        # Baseline half-life (minutes) for mid-mastery
        self.base_hl_minutes = 180.0  # 3 hours baseline; tune per subject/domain

        # Feature weights (log-space) — placeholders; learnable later:
        self.w_mastery = 1.50   # higher mastery → longer half-life
        self.w_correct = 0.35   # last answer correct → longer half-life
        self.w_bias = 0.00

    def estimate_half_life_minutes(
        self,
        *,
        mastery: float,
        last_correct: bool
    ) -> float:
        """
        h = base_hl * exp( w_bias + w_mastery * f(mastery) + w_correct * I(last_correct) )
        f(mastery) uses logit to expand near 0/1, then clipped for stability.
        """
        # Stabilize mastery transform
        m = min(max(mastery, 1e-3), 1.0 - 1e-3)
        logit_m = math.log(m / (1.0 - m))
        z = self.w_bias + self.w_mastery * (logit_m / 2.0) + self.w_correct * (1.0 if last_correct else -0.5)
        h = self.base_hl_minutes * math.exp(z)
        # Clamp to reasonable [5 min, 14 days]
        return float(min(max(h, 5.0), 14.0 * 24.0 * 60.0))

    def optimal_spacing_minutes(
        self,
        *,
        mastery: float,
        last_correct: bool,
        retention_target: float = 0.85
    ) -> Dict[str, Any]:
        """
        Solve exp(-Δt / h) = retention_target → Δt = -h * ln(retention_target)
        """
        retention = min(max(retention_target, 0.50), 0.99)
        h = self.estimate_half_life_minutes(mastery=mastery, last_correct=last_correct)
        gap = -h * math.log(retention)
        # Clamp to [1 min, 30 days]
        gap = float(min(max(gap, 1.0), 30.0 * 24.0 * 60.0))
        return {
            "half_life_minutes": h,
            "next_review_in_minutes": gap,
            "retention_target": retention,
        }
