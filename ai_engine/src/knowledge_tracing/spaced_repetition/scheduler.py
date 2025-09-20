# ai_engine/src/knowledge_tracing/spaced_repetition/scheduler.py
import math
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger("spaced_repetition")

class HalfLifeRegressionScheduler:
    """
    Implements Half-Life Regression model for spaced repetition.

    Estimates optimal review intervals based on item difficulty,
    student ability, and forgetting curves.
    """

    def __init__(self, alpha: float = 4.0, beta: float = -0.5):
        self.alpha = alpha
        self.beta = beta

    def estimate_half_life(self, difficulty: float, ability: float, features: dict) -> float:
        """
        Estimate half-life time (hours) using regression formula.

        Args:
            difficulty (float): Item difficulty (0-1)
            ability (float): Student ability (0-1)
            features (dict): Optional additional features

        Returns:
            float: predicted half-life in hours
        """
        score = self.alpha * difficulty + self.beta * ability
        # Additional feature adjustments if needed
        logger.debug(f"HLR estimate: difficulty={difficulty}, ability={ability}, score={score}")
        half_life = math.exp(score)
        return half_life

    def next_review_time(self, last_review: datetime, half_life_hours: float) -> datetime:
        """
        Compute next review datetime

        Args:
            last_review (datetime): datetime of last review
            half_life_hours (float): half-life interval in hours

        Returns:
            datetime: next review datetime
        """
        return last_review + timedelta(hours=half_life_hours)
