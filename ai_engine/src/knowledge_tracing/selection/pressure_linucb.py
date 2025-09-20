# ai_engine/src/knowledge_tracing/selection/pressure_linucb.py
from __future__ import annotations
import numpy as np
import logging
from typing import List, Tuple, Dict, Any

from .bandit_policy import LinUCBPolicy, BanditContext

logger = logging.getLogger("pressure_linucb")

class PressureAwareLinUCB(LinUCBPolicy):
    """
    LinUCB variant that augments context feature vectors with stress_level and cognitive_load,
    handling dimensionality changes and fallback for legacy models.
    """

    def select_with_pressure(self, contexts: List[BanditContext]) -> Tuple[str, Dict[str, Any]]:
        """
        Selects best arm given bandit contexts injected with pressure features.

        Args:
          contexts (List[BanditContext]): List of bandit candidate contexts.

        Returns:
          (arm_id, diagnostics) tuple, arm_id is string id of selected arm.
        """
        try:
            enhanced_contexts: List[Tuple[str, np.ndarray]] = []
            for ctx in contexts:
                base_vec = ctx.feature_vector()  # base d-dimensional vector
                stress = ctx.features.get("stress_level", 0.0)
                load = ctx.features.get("cognitive_load", 0.0)
                extended_vec = np.concatenate([base_vec, [stress, load]])
                enhanced_contexts.append((ctx.arm_id, extended_vec))

            new_d = enhanced_contexts[0][1].size
            if new_d != self.d:
                self._resize_to(new_d)

            return super().select_with_matrices(enhanced_contexts)
        except Exception as e:
            logger.exception("PressureAwareLinUCB selection failed, falling back")
            return super().select(contexts)

    def _resize_to(self, new_dim: int):
        "Resize internal matrices A and b preserving existing data."
        old_dim = self.d
        old_A = self.A.copy()
        old_b = self.b.copy()

        self.d = new_dim
        self.A = np.eye(new_dim)
        self.b = np.zeros(new_dim)
        self.A[:old_dim, :old_dim] = old_A
        self.b[:old_dim] = old_b

        logger.info(f"Resized LinUCB internal dimension: from {old_dim} to {new_dim}")
