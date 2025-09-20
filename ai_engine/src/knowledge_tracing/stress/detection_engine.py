# ai_engine/src/knowledge_tracing/stress/detection_engine.py
from __future__ import annotations
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger("stress_detection")

@dataclass
class StressIndicators:
    """Detailed indicators contributing to stress estimation."""
    response_time_variance: float
    error_streak_length: int
    hesitation_duration_ms: float
    keystroke_deviation_score: float
    fatigue_estimate: float
    timestamp: datetime

@dataclass
class StressLevel:
    """Normalized stress estimation output."""
    level: float                # Normalized intensity in [0,1]
    confidence: float           # Confidence in the estimation [0,1]
    indicators: List[str]       # Triggered indicators keys
    intervention: Optional[str] # Intervention needed: None, mild, moderate, high

class MultiModalStressDetector:
    """
    Multi-modal stress detection engine synthesizing behavioral cues:
    - Response time variance ratio
    - Consecutive error streak lengths
    - Hesitation durations tracking
    - Keystroke pattern deviation metrics
    - Fatigue level inferred from window fullness

    Provides robust fallbacks for production stability,
    interpretable warning flags, and graduated intervention levels.
    """

    def __init__(self, window_size: int = 12):
        """
        Initialize detector with rolling analysis window size.

        Args:
            window_size (int): Number of recent question attempts to consider.
        """
        self.window_size = window_size
        self.rt_history: List[float] = []
        self.acc_history: List[bool] = []
        self.thresholds = {
            "rt_var_mild": 1.5,
            "rt_var_mod": 2.5,
            "rt_var_high": 4.0,
            "error_streak_mild": 3,
            "error_streak_mod": 5,
            "hesitation_mild": 2000.0,     # milliseconds
            "hesitation_high": 5000.0,    # milliseconds
            "keystroke_dev_threshold": 0.6,
            "fatigue_threshold": 0.75
        }

    def detect(self, response_time: float, correct: bool,
               hesitation_ms: float = 0.0,
               keystroke_dev: float = 0.0) -> StressLevel:
        """
        Estimate stress level for a single interaction.

        Parameters:
            response_time (float): Time taken for last response (ms)
            correct (bool): Whether last response was correct
            hesitation_ms (float): Hesitation duration before response (ms)
            keystroke_dev (float): Keystroke deviation metric [0,1]

        Returns:
            StressLevel: comprehensive stress estimation
        """
        # --- Update rolling history buffers ---
        self.rt_history.append(response_time)
        self.acc_history.append(correct)
        if len(self.rt_history) > self.window_size:
            self.rt_history.pop(0)
            self.acc_history.pop(0)

        # --- Response time variance ratio calculation ---
        if len(self.rt_history) > 1:
            baseline_var = np.var(self.rt_history[:-1])
            # Prevent division by extremely small baseline variance
            baseline_var = max(baseline_var, 1e-6)
            current_var = np.var(self.rt_history)
            var_ratio = current_var / baseline_var
        else:
            var_ratio = 1.0  # Default to neutral ratio

        # --- Consecutive error streak ---
        error_streak = 0
        for entry in reversed(self.acc_history):
            if not entry:
                error_streak += 1
            else:
                break

        # --- Fatigue estimate based on window fullness ---
        fatigue = min(1.0, len(self.rt_history) / self.window_size)

        # --- Compute composite stress score ---
        score = 0.0
        indicators = []

        # 1. RT variance contribution
        if var_ratio >= self.thresholds["rt_var_high"]:
            indicators.append("rt_variance_high")
            score += 0.4
        elif var_ratio >= self.thresholds["rt_var_mod"]:
            indicators.append("rt_variance_medium")
            score += 0.3
        elif var_ratio >= self.thresholds["rt_var_mild"]:
            indicators.append("rt_variance_mild")
            score += 0.15

        # 2. Error streak contribution
        if error_streak >= self.thresholds["error_streak_mod"]:
            indicators.append("error_streak_high")
            score += 0.3
        elif error_streak >= self.thresholds["error_streak_mild"]:
            indicators.append("error_streak_mild")
            score += 0.15

        # 3. Hesitation contribution
        if hesitation_ms >= self.thresholds["hesitation_high"]:
            indicators.append("hesitation_high")
            score += 0.2
        elif hesitation_ms >= self.thresholds["hesitation_mild"]:
            indicators.append("hesitation_mild")
            score += 0.1

        # 4. Keystroke deviation contribution
        if keystroke_dev >= self.thresholds["keystroke_dev_threshold"]:
            indicators.append("keystroke_deviation")
            score += 0.1

        # 5. Fatigue contribution
        if fatigue >= self.thresholds["fatigue_threshold"]:
            indicators.append("fatigue")
            score += 0.1

        # --- Normalize score and confidence ---
        stress_level_norm = min(1.0, score)
        confidence = min(1.0, len(self.rt_history) / self.window_size)

        # --- Determine intervention level ---
        if stress_level_norm >= 0.7:
            intervention = "high"
        elif stress_level_norm >= 0.4:
            intervention = "moderate"
        elif stress_level_norm >= 0.2:
            intervention = "mild"
        else:
            intervention = None

        # --- Logging for transparency and debugging ---
        logger.debug(f"[StressDetection] RT variance ratio: {var_ratio:.2f}, Error streak: {error_streak}, "
                     f"Hesitation: {hesitation_ms}ms, Keystroke Dev: {keystroke_dev:.2f}, Fatigue: {fatigue:.2f}, "
                     f"Score: {score:.2f}, Level: {stress_level_norm:.2f}, Intervention: {intervention}")

        return StressLevel(
            level=stress_level_norm,
            confidence=confidence,
            indicators=indicators,
            intervention=intervention
        )
