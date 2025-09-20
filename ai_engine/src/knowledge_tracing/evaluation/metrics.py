# ai_engine/src/knowledge_tracing/evaluation/metrics.py
import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict
from sklearn.metrics import roc_auc_score, accuracy_score
from scipy import stats

class BKTEvaluationSuite:
    """
    Computes:
      - Next-step prediction AUC and Accuracy
      - Brier score and calibration error via reliability bins
      - Mastery trajectory sanity checks (trend score)
    NOTE: Wire a data provider to feed interactions and trajectories per window.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    # Public entrypoint – in production inject a data provider
    def evaluate_window(
        self,
        concept_id: Optional[str] = None,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Placeholder: replace with actual data pull from logs
        y_true, y_prob, trajectories = self._mock_pull(concept_id, start_ts, end_ts)

        # Next-step metrics
        auc = self._safe_auc(y_true, y_prob)
        acc = accuracy_score(y_true, (np.array(y_prob) > 0.5).astype(int))

        # Calibration
        brier, ece = self._brier_and_ece(y_true, y_prob, self.n_bins)

        # Trajectory sanity
        traj_validity = self._trajectory_validity(trajectories)

        recommendation = "PASS" if (auc >= 0.75 and brier <= 0.20 and ece <= 0.10 and traj_validity >= 0.60) else "NEEDS_IMPROVEMENT"

        return {
            "next_step_auc": float(auc),
            "next_step_accuracy": float(acc),
            "brier_score": float(brier),
            "calibration_error": float(ece),
            "trajectory_validity": float(traj_validity),
            "recommendation": recommendation,
            "details": {
                "n_samples": int(len(y_true)),
                "n_trajectories": int(len(trajectories)),
                "bins": int(self.n_bins),
            },
        }

    def _safe_auc(self, y_true: List[int], y_prob: List[float]) -> float:
        y = np.array(y_true, dtype=int)
        p = np.array(y_prob, dtype=float)
        # If y has only one class, AUC is undefined; return 0.5
        if len(np.unique(y)) < 2:
            return 0.5
        try:
            return float(roc_auc_score(y, p))
        except Exception:
            return 0.5

    def _brier_and_ece(self, y_true: List[int], y_prob: List[float], n_bins: int) -> Tuple[float, float]:
        y = np.array(y_true, dtype=float)
        p = np.clip(np.array(y_prob, dtype=float), 1e-6, 1.0 - 1e-6)

        # Brier score
        brier = float(np.mean((p - y) ** 2))

        # Reliability bins for Expected Calibration Error (ECE)
        bins = np.linspace(0.0, 1.0, n_bins + 1)
        idx = np.digitize(p, bins) - 1
        ece = 0.0
        for b in range(n_bins):
            mask = idx == b
            if not np.any(mask):
                continue
            conf = float(np.mean(p[mask]))
            acc = float(np.mean(y[mask]))
            ece += (np.sum(mask) / len(y)) * abs(acc - conf)
        return brier, float(ece)

    def _trajectory_validity(self, trajectories: Dict[str, List[float]]) -> float:
        """
        Valid if trend is generally increasing after correct sequences.
        Trend score via slope * R^2; require positive trend more often than not.
        """
        if not trajectories:
            return 0.0
        valid, total = 0, 0
        for _, seq in trajectories.items():
            if len(seq) < 5:
                continue
            x = np.arange(len(seq))
            slope, _, r, _, _ = stats.linregress(x, seq)
            score = slope * (r ** 2)
            if score > 0.0:
                valid += 1
            total += 1
        return float(valid / total) if total > 0 else 0.0

    def _mock_pull(
        self, concept_id: Optional[str], start_ts: Optional[str], end_ts: Optional[str]
    ) -> Tuple[List[int], List[float], Dict[str, List[float]]]:
        # Replace with actual data source: question_interactions + predicted probs per step
        # Mock small, balanced sample for scaffolding
        y_true = [0, 1, 1, 0, 1, 0, 1, 1]
        y_prob = [0.2, 0.7, 0.8, 0.4, 0.75, 0.3, 0.85, 0.65]
        trajectories = {
            "studentA_kinematics": [0.40, 0.48, 0.60, 0.68, 0.75, 0.80],
            "studentB_kinematics": [0.55, 0.50, 0.52, 0.57, 0.61, 0.64],
        }
        return y_true, y_prob, trajectories
