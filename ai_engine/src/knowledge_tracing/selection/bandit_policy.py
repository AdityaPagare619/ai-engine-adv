# ai_engine/src/knowledge_tracing/selection/bandit_policy.py
from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Any

class BanditContext:
    def __init__(self, arm_id: str, features: Dict[str, Any]):
        self.arm_id = arm_id
        self.features = features

    def feature_vector(self) -> np.ndarray:
        # Order matters; extended with pressure and scoring
        order = [
            "difficulty",
            "estimated_time_ms",
            "mastery_level",
            "stress_level",
            "cognitive_load",
            "correct_score",
            "incorrect_score"
        ]
        return np.array([float(self.features.get(k, 0.0)) for k in order], dtype=np.float64)

class LinUCBPolicy:
    def __init__(self, alpha: float = 0.6, d: int = 7):
        self.alpha = alpha
        self.d = d
        self.A = np.eye(self.d)
        self.b = np.zeros(self.d)

    def select(self, contexts: List[BanditContext]) -> Tuple[str, Dict[str, float]]:
        extended = [(c.arm_id, c.feature_vector()) for c in contexts]
        return self.select_with_matrices(extended)

    def select_with_matrices(self, contexts: List[Tuple[str, np.ndarray]]) -> Tuple[str, Dict[str, float]]:
        A_inv = np.linalg.inv(self.A)
        theta = A_inv.dot(self.b)

        best_p = float("-inf")
        chosen = None
        diagnostics: Dict[str, float] = {}

        for arm_id, x in contexts:
            x = x.reshape((-1, 1))
            ucb = float(theta.dot(x)) + self.alpha * np.sqrt(float(x.T.dot(A_inv).dot(x)))
            diagnostics[arm_id] = ucb
            if ucb > best_p:
                best_p = ucb
                chosen = arm_id

        return chosen, diagnostics

    def update(self, chosen_arm_vec: np.ndarray, reward: float):
        x = chosen_arm_vec.reshape((-1, 1))
        self.A += x.dot(x.T)
        self.b += reward * x.flatten()
