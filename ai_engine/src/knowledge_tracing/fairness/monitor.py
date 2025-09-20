# ai_engine/src/knowledge_tracing/fairness/monitor.py
from typing import List, Dict, Optional
import logging
import numpy as np

logger = logging.getLogger("fairness_monitor")

class FairnessMonitor:
    """
    Monitors demographic parity bias and reading ability bias in mastery estimates.

    Tracks statistics for defined groups and issues alerts when disparities grow.
    """

    def __init__(self, protected_groups: Optional[List[str]] = None):
        self.protected_groups = protected_groups or []
        self.group_stats = {}

    def update_stats(self, group: str, mastery_scores: List[float]):
        if group not in self.group_stats:
            self.group_stats[group] = []

        self.group_stats[group].extend(mastery_scores)

    def check_parity(self) -> Dict[str, float]:
        """
        Returns a dictionary of group-wise average mastery and disparity measures
        """
        averages = {}
        for group, scores in self.group_stats.items():
            if scores:
                avg = np.mean(scores)
                averages[group] = avg
            else:
                averages[group] = float('nan')

        if len(averages) < 2:
            return averages  # Not enough groups to compare

        max_avg = max(averages.values())
        min_avg = min(averages.values())
        disparity = max_avg - min_avg

        logger.info(f"FairnessMonitor: Group averages: {averages}, Disparity: {disparity}")
        return {
            "averages": averages,
            "disparity": disparity
        }

    def generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on current disparity.
        """
        results = self.check_parity()
        recs = []

        if "disparity" in results:
            if results["disparity"] > 0.1:
                recs.append("Investigate feature bias and retrain model")
            else:
                recs.append("Bias levels acceptable")

        return recs
