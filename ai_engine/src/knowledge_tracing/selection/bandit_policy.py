# ai_engine/src/knowledge_tracing/selection/bandit_policy.py
from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Any

class BanditContext:
    """
    Wrapper for context vectors for a single candidate arm.
    Stores arm_id and feature dictionary.
    """

    def __init__(self, arm_id: str, features: Dict[str, Any]):
        self.arm_id = arm_id
        self.features = features

    def feature_vector(self) -> np.ndarray:
        """
        Extract numeric feature vector (e.g. difficulty, mastery etc.) in fixed order.
        Note: This must match LinUCB internal assumption.
        """
        # Assuming fixed feature keys and order
        feature_order = ["difficulty", "estimated_time_ms", "mastery_level"]
        vec = np.array([self.features.get(k, 0.0) for k in feature_order], dtype=np.float64)
        return vec

class LinUCBPolicy:
    """
    Classic LinUCB policy for contextual bandits.
    """
    def __init__(self, alpha: float = 0.6):
        """
        Initialize LinUCB with exploration parameter alpha.
        """
        self.alpha = alpha
        self.d = 3  # baseline dimension, adjust if extended features present
        self.A = np.eye(self.d)
        self.b = np.zeros(self.d)

    def select(self, contexts: List[BanditContext]) -> Tuple[str, Dict[str, float]]:
        """
        Select arm with highest upper confidence bound.

        Returns tuple (arm_id, diagnostics)
        """
        try:
            extended = [(ctx.arm_id, ctx.feature_vector()) for ctx in contexts]
            return self.select_with_matrices(extended)
        except Exception:
            # Fallback to random
            return contexts[0].arm_id, {}

    def select_with_matrices(self, contexts: List[Tuple[str, np.ndarray]]) -> Tuple[str, Dict[str, float]]:
        """
        Select arm given explicit arm vectors.

        Args:
          contexts: List of (arm_id, feature_vector)

        Returns:
          (arm_id, diagnostics)
        """
        A_inv = np.linalg.inv(self.A)
        theta = A_inv.dot(self.b)

        max_ucb = float('-inf')
        chosen_arm = None
        diagnostics = {}

        for arm_id, x in contexts:
            x = x.reshape((-1, 1))
            p = float(theta.dot(x)) + self.alpha * np.sqrt(float(x.T.dot(A_inv).dot(x)))
            diagnostics[arm_id] = p
            if p > max_ucb:
                max_ucb = p
                chosen_arm = arm_id

        return chosen_arm, diagnostics

    def update(self, chosen_arm_vec: np.ndarray, reward: float):
        """
        Update model matrices A and b according to observed reward.
        """
        x = chosen_arm_vec.reshape((-1, 1))
        self.A += x.dot(x.T)
        self.b += reward * x.flatten()
