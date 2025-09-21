# ai_engine/src/knowledge_tracing/fairness/monitor.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger("fairness_monitor")

Key = Tuple[str, str]  # (exam_code, subject)

class FairnessMonitor:
    """
    Tracks mastery/score distributions segmented by (exam_code, subject) and group keys,
    enabling per-exam audits and avoiding masked disparities across subjects.
    """
    def __init__(self):
        self.group_stats: Dict[Key, Dict[str, List[float]]] = {}

    def update_stats(self, exam_code: str, subject: str, group: str, mastery_scores: List[float]):
        key: Key = (exam_code or "JEE_Mains", subject or "generic")
        if key not in self.group_stats:
            self.group_stats[key] = {}
        if group not in self.group_stats[key]:
            self.group_stats[key][group] = []
        self.group_stats[key][group].extend(mastery_scores)

    def check_parity(self, exam_code: str = "JEE_Mains", subject: str = "generic") -> Dict[str, float]:
        key: Key = (exam_code, subject)
        groups = self.group_stats.get(key, {})
        if not groups:
            return {"averages": {}, "disparity": 0.0}
        avgs = {g: float(np.mean(vals)) if len(vals) else float("nan") for g, vals in groups.items()}
        if len(avgs) < 2:
            return {"averages": avgs, "disparity": 0.0}
        disparity = max(avgs.values()) - min(avgs.values())
        logger.info(f"[Fairness] {key} avgs={avgs} disparity={disparity:.4f}")
        return {"averages": avgs, "disparity": float(disparity)}

    def generate_recommendations(self, disparity: float) -> List[str]:
        if disparity > 0.15:
            return ["Investigate feature bias and retrain per-exam head", "Review time allocation skew by group"]
        if disparity > 0.08:
            return ["Monitor drift and audit selection thresholds"]
        return ["Bias levels acceptable"]
