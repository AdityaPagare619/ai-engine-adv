# ai_engine/src/knowledge_tracing/selection/pressure_linucb.py
from __future__ import annotations
import numpy as np
import logging
from typing import List, Tuple, Dict, Any

from ai_engine.src.knowledge_tracing.selection.bandit_policy import LinUCBPolicy, BanditContext

logger = logging.getLogger("pressure_linucb")

class PressureAwareLinUCB(LinUCBPolicy):
    """
    LinUCB that consumes extended feature vectors (stress/load/scoring/time),
    safely resizes matrices when feature dimension changes, and exposes
    reward updates normalized by observed time-to-answer.
    """

    def select_with_pressure(self, contexts: List[BanditContext]) -> Tuple[str, Dict[str, Any]]:
        try:
            enhanced: List[Tuple[str, np.ndarray]] = []
            for ctx in contexts:
                x = ctx.feature_vector()
                enhanced.append((ctx.arm_id, x))
            new_d = enhanced[0][1].size
            if new_d != self.d:
                self._resize_to(new_d)
            return super().select_with_matrices(enhanced)
        except Exception:
            logger.exception("PressureAwareLinUCB selection failed; fallback to base")
            return super().select(contexts)

    def update_with_outcome(self, ctx: BanditContext, correct: bool, observed_time_ms: float):
        """
        Computes reward as expected score per unit time (per 30s) using exam scoring
        from context, then updates LinUCB with the chosen arm's feature vector.
        """
        try:
            correct_score = float(ctx.features.get("correct_score", 1.0))
            incorrect_score = float(ctx.features.get("incorrect_score", 0.0))
            score = correct_score if correct else incorrect_score
            time_norm = max(1000.0, float(observed_time_ms))
            reward = (score / time_norm) * 30000.0  # normalize to 30s window

            x = ctx.feature_vector()
            if x.size != self.d:
                self._resize_to(x.size)
            self.update(x, reward)
        except Exception:
            logger.exception("PressureAwareLinUCB update_with_outcome failed")

    def _resize_to(self, new_dim: int):
        old_A, old_b, old_d = self.A.copy(), self.b.copy(), self.d
        self.d = new_dim
        self.A = np.eye(new_dim)
        self.b = np.zeros(new_dim)
        self.A[:old_d, :old_d] = old_A
        self.b[:old_d] = old_b
        logger.info(f"Resized LinUCB from {old_d} to {new_dim}")
