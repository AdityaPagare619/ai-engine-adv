# ai_engine/src/knowledge_tracing/bkt/bkt_engine.py
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import logging
import math
from ai_engine.src.config.exam_config import EXAM_CONFIGS

logger = logging.getLogger("bkt_engine")

class AdaptiveTimeThreshold:
    """
    Adaptive time pressure threshold that adjusts based on student performance history
    and current mastery level to better handle time-constrained scenarios.
    """
    def __init__(self):
        self.base_threshold = 0.7  # Base threshold for time pressure
        self.history_size = 5      # Number of recent responses to consider
        self.response_history: Dict[str, List[Tuple[bool, float]]] = {}  # student_id -> [(correct, time_pressure)]
        
    def get_adaptive_threshold(self, student_id: str, mastery: float, time_pressure: float) -> float:
        """
        Calculate adaptive time pressure threshold based on:
        1. Student's recent performance under time pressure
        2. Current mastery level
        3. Baseline threshold
        """
        # Initialize history if needed
        if student_id not in self.response_history:
            self.response_history[student_id] = []
            
        history = self.response_history[student_id]
        
        # If we have enough history, calculate adaptation
        if len(history) >= 3:
            # Calculate success rate under time pressure
            time_pressured_responses = [(correct, tp) for correct, tp in history if tp > self.base_threshold]
            if time_pressured_responses:
                success_rate = sum(1 for correct, _ in time_pressured_responses if correct) / len(time_pressured_responses)
                
                # Adjust threshold based on success under pressure
                if success_rate > 0.7:  # Student handles pressure well
                    threshold_modifier = 0.15  # Increase threshold (less sensitive)
                elif success_rate < 0.3:  # Student struggles under pressure
                    threshold_modifier = -0.15  # Decrease threshold (more sensitive)
                else:
                    threshold_modifier = 0.0  # Neutral
                    
                # Mastery also affects threshold - higher mastery can handle more pressure
                mastery_modifier = (mastery - 0.5) * 0.2  # -0.1 to +0.1 range
                
                # Calculate final adaptive threshold
                adaptive_threshold = self.base_threshold + threshold_modifier + mastery_modifier
                return max(0.4, min(0.9, adaptive_threshold))  # Clamp between 0.4-0.9
        
        # Default to base threshold with slight mastery adjustment if not enough history
        mastery_modifier = (mastery - 0.5) * 0.1
        return max(0.4, min(0.9, self.base_threshold + mastery_modifier))
    
    def update_history(self, student_id: str, correct: bool, time_pressure: float):
        """Update student's response history"""
        if student_id not in self.response_history:
            self.response_history[student_id] = []
            
        history = self.response_history[student_id]
        history.append((correct, time_pressure))
        
        # Keep only recent history
        if len(history) > self.history_size:
            self.response_history[student_id] = history[-self.history_size:]

class BKTEngine:
    """
    BKT with modifiers from stress/load/time pressure and per-exam priors.
    Enhanced with adaptive time pressure handling.
    """
    def __init__(self, exam_code: str = "JEE_Mains"):
        self.exam_code = exam_code
        self.config = EXAM_CONFIGS.get(exam_code, EXAM_CONFIGS["JEE_Mains"])
        # Example priors; in production, load per skill/topic
        self.prior = 0.6
        self.learn = 0.2
        self.slip = 0.1
        self.guess = 0.2
        self.time_threshold = AdaptiveTimeThreshold()
        self.student_recovery_factor: Dict[str, float] = {}  # Tracks recovery needs per student

    def update(self, student_response: Dict[str, Any], **context) -> Dict[str, Any]:
        correct = bool(student_response.get("correct", False))
        stress = float(context.get("stress_level", 0.0))
        load = float(context.get("cognitive_load", 0.0))
        time_press = float(context.get("time_pressure_factor", 1.0))
        student_id = student_response.get("student_id", "unknown")
        
        # Get adaptive time pressure threshold
        adaptive_threshold = self.time_threshold.get_adaptive_threshold(
            student_id, self.prior, time_press
        )
        
        # Apply adaptive threshold to determine effective time pressure
        effective_time_press = time_press if time_press > adaptive_threshold else time_press * 0.7
        
        # Apply recovery factor if available
        if student_id in self.student_recovery_factor:
            recovery = self.student_recovery_factor[student_id]
            effective_time_press *= max(0.7, 1.0 - recovery)
            # Gradually reduce recovery factor
            self.student_recovery_factor[student_id] = max(0.0, recovery - 0.1)
        
        # Modulate slip/guess with stress/load and effective time pressure
        slip = min(0.4, max(0.01, self.slip * (1.0 + 0.3 * stress + 0.2 * load)))
        guess = min(0.5, max(0.01, self.guess * (1.0 + 0.1 * stress)))

        # Learning rate modulated by load and effective time pressure with improved scaling
        time_press_factor = math.exp(-effective_time_press) if effective_time_press > 0.8 else (1.0 + 0.1 * (2.0 - effective_time_press))
        learn = min(0.5, max(0.05, self.learn * (1.0 - 0.2 * load) * time_press_factor))

        pL = self.prior
        if correct:
            num = pL * (1 - slip)
            den = pL * (1 - slip) + (1 - pL) * guess
        else:
            num = pL * slip
            den = pL * slip + (1 - pL) * (1 - guess)
        post = num / den if den > 1e-9 else pL

        p_mastery = post + (1 - post) * learn
        p_mastery = max(0.0, min(1.0, p_mastery))
        
        # Update time pressure history
        self.time_threshold.update_history(student_id, correct, time_press)
        
        # If student is struggling under time pressure, activate recovery mode
        if time_press > adaptive_threshold and not correct and student_id not in self.student_recovery_factor:
            self.student_recovery_factor[student_id] = 0.3  # Initial recovery factor
        
        self.prior = p_mastery  # for example, single-skill scenario
        logger.debug(f"[BKT] prior→{pL:.3f} post→{post:.3f} mastery→{p_mastery:.3f} (slip={slip:.3f}, guess={guess:.3f}, learn={learn:.3f}, time_press→{time_press:.2f}, effective→{effective_time_press:.2f})")
        return {
            "mastery": float(p_mastery),
            "adaptive_time_threshold": float(adaptive_threshold),
            "effective_time_pressure": float(effective_time_press)
        }
