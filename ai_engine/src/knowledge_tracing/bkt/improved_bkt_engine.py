# ai_engine/src/knowledge_tracing/bkt/improved_bkt_engine.py
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import logging
import math
import numpy as np
from ai_engine.src.config.exam_config import EXAM_CONFIGS

logger = logging.getLogger("improved_bkt_engine")

class ConceptMasteryTracker:
    """
    Tracks mastery for multiple concepts with cross-concept transfer learning
    """
    def __init__(self):
        self.concept_masteries: Dict[str, float] = {}
        self.concept_attempts: Dict[str, int] = {}
        self.related_concepts = {
            # Physics concepts
            "mechanics": ["thermodynamics", "calculus"],
            "thermodynamics": ["mechanics", "calculus"],
            # Chemistry concepts
            "organic_chemistry": ["calculus"],
            # Biology concepts
            "genetics": ["organic_chemistry"],
            # Math concepts
            "calculus": ["mechanics", "thermodynamics"]
        }
    
    def get_concept_prior(self, concept: str) -> float:
        """Get concept-specific prior with transfer learning"""
        if concept not in self.concept_masteries:
            # Calculate initial prior based on related concepts
            related = self.related_concepts.get(concept, [])
            if related:
                related_masteries = [self.concept_masteries.get(c, 0.2) for c in related if c in self.concept_masteries]
                if related_masteries:
                    # Transfer learning: use 30% of related concept mastery
                    transfer_boost = np.mean(related_masteries) * 0.3
                    initial_prior = min(0.4, 0.2 + transfer_boost)  # Cap at 0.4
                else:
                    initial_prior = 0.2  # Default low prior
            else:
                initial_prior = 0.2
            
            self.concept_masteries[concept] = initial_prior
            self.concept_attempts[concept] = 0
            
        return self.concept_masteries[concept]
    
    def update_concept_mastery(self, concept: str, new_mastery: float):
        """Update mastery and attempt count"""
        self.concept_masteries[concept] = new_mastery
        self.concept_attempts[concept] = self.concept_attempts.get(concept, 0) + 1
    
    def get_confidence_weight(self, concept: str) -> float:
        """Get confidence weight based on number of attempts"""
        attempts = self.concept_attempts.get(concept, 0)
        # Confidence increases with attempts, plateaus at 20 attempts
        return min(1.0, attempts / 20.0)

class StudentAdaptiveProfile:
    """
    Maintains student-specific adaptive parameters based on their learning patterns
    """
    def __init__(self):
        self.learning_rates: Dict[str, float] = {}  # Per student learning rates
        self.stress_tolerance: Dict[str, float] = {}  # How well student handles stress
        self.recovery_patterns: Dict[str, List[float]] = {}  # Recovery after mistakes
        self.performance_history: Dict[str, List[bool]] = {}  # Recent performance
        
    def get_adaptive_learning_rate(self, student_id: str, base_rate: float) -> float:
        """Get adaptive learning rate for student"""
        if student_id not in self.learning_rates:
            self.learning_rates[student_id] = base_rate
            return base_rate
        
        # Adapt based on recent performance
        if student_id in self.performance_history:
            recent_perf = self.performance_history[student_id][-10:]  # Last 10 responses
            if len(recent_perf) >= 5:
                success_rate = sum(recent_perf) / len(recent_perf)
                
                if success_rate > 0.8:  # High performer
                    adaptive_rate = min(0.5, base_rate * 1.3)  # Learn faster
                elif success_rate < 0.4:  # Struggling student  
                    adaptive_rate = min(0.4, base_rate * 1.1)  # Slight boost to help
                else:
                    adaptive_rate = base_rate  # Standard rate
                
                self.learning_rates[student_id] = adaptive_rate
                return adaptive_rate
        
        return self.learning_rates[student_id]
    
    def get_stress_modifier(self, student_id: str, stress_level: float) -> float:
        """Get stress impact modifier for student"""
        if student_id not in self.stress_tolerance:
            # Initialize with neutral tolerance
            self.stress_tolerance[student_id] = 0.5
        
        tolerance = self.stress_tolerance[student_id]
        
        # Students with high tolerance are less affected by stress
        # Students with low tolerance are more affected
        base_impact = stress_level * 0.15  # Reduced from 0.3
        
        # Optimal stress zone (0.2-0.4) can actually improve performance
        if 0.2 <= stress_level <= 0.4:
            stress_modifier = -0.05 * (1 - tolerance)  # Slight boost for tolerant students
        elif stress_level > 0.6:
            stress_modifier = base_impact * (2 - tolerance)  # More impact for intolerant students
        else:
            stress_modifier = base_impact * (1.5 - tolerance)
        
        return stress_modifier
    
    def update_student_profile(self, student_id: str, correct: bool, stress_level: float):
        """Update student profile based on performance"""
        # Update performance history
        if student_id not in self.performance_history:
            self.performance_history[student_id] = []
        
        self.performance_history[student_id].append(correct)
        if len(self.performance_history[student_id]) > 20:  # Keep last 20 responses
            self.performance_history[student_id] = self.performance_history[student_id][-20:]
        
        # Update stress tolerance based on performance under stress
        if stress_level > 0.5:  # High stress situation
            current_tolerance = self.stress_tolerance.get(student_id, 0.5)
            
            if correct:  # Performed well under stress
                new_tolerance = min(1.0, current_tolerance + 0.02)
            else:  # Struggled under stress
                new_tolerance = max(0.1, current_tolerance - 0.01)
            
            self.stress_tolerance[student_id] = new_tolerance

class ImprovedBKTEngine:
    """
    Enhanced BKT Engine with:
    1. Lower, concept-specific initial priors
    2. Adaptive learning rates per student
    3. Better context integration
    4. Recovery mechanisms
    5. Multi-concept tracking with transfer learning
    """
    def __init__(self, exam_code: str = "JEE_Mains"):
        self.exam_code = exam_code
        self.config = EXAM_CONFIGS.get(exam_code, EXAM_CONFIGS["JEE_Mains"])
        
        # Improved base parameters
        self.base_prior = 0.25  # Lowered from 0.6
        self.base_learn = 0.35  # Increased from 0.2
        self.base_slip = 0.12   # Slightly increased
        self.base_guess = 0.18  # Slightly decreased
        
        # Advanced components
        self.concept_tracker = ConceptMasteryTracker()
        self.student_profiles = StudentAdaptiveProfile()
        
        # Recovery mechanism
        self.student_struggle_count: Dict[str, int] = {}
        self.recovery_boost_active: Dict[str, float] = {}
        
        logger.info(f"[ImprovedBKT] Initialized for {exam_code} with enhanced parameters")

    def get_difficulty_adjusted_parameters(self, difficulty: float) -> Tuple[float, float]:
        """Adjust slip and guess based on question difficulty"""
        # Higher difficulty -> higher slip, lower guess
        difficulty_factor = difficulty  # 0.0 to 1.0
        
        adjusted_slip = self.base_slip * (1 + difficulty_factor * 0.8)  # Up to 80% increase
        adjusted_guess = self.base_guess * (1 - difficulty_factor * 0.4)  # Up to 40% decrease
        
        # Clamp values
        adjusted_slip = max(0.05, min(0.35, adjusted_slip))
        adjusted_guess = max(0.08, min(0.35, adjusted_guess))
        
        return adjusted_slip, adjusted_guess

    def update(self, student_response: Dict[str, Any], concept: str = "general", **context) -> Dict[str, Any]:
        """
        Enhanced BKT update with multi-concept tracking and adaptive parameters
        """
        correct = bool(student_response.get("correct", False))
        stress = float(context.get("stress_level", 0.0))
        load = float(context.get("cognitive_load", 0.0))
        time_press = float(context.get("time_pressure_factor", 1.0))
        difficulty = float(context.get("difficulty", 0.5))
        student_id = student_response.get("student_id", "unknown")
        
        # Get concept-specific prior with transfer learning
        prior_mastery = self.concept_tracker.get_concept_prior(concept)
        
        # Get adaptive learning rate for this student
        adaptive_learn = self.student_profiles.get_adaptive_learning_rate(student_id, self.base_learn)
        
        # Get difficulty-adjusted parameters
        slip, guess = self.get_difficulty_adjusted_parameters(difficulty)
        
        # Apply context factors (less aggressive than before)
        stress_modifier = self.student_profiles.get_stress_modifier(student_id, stress)
        
        # Cognitive load impact (reduced)
        load_modifier = load * 0.1  # Reduced from 0.2
        
        # Time pressure impact (with adaptation)
        if time_press > 1.2:  # High time pressure
            time_modifier = (time_press - 1.0) * 0.08  # Reduced from higher values
        else:  # Normal or low time pressure
            time_modifier = -(1.0 - time_press) * 0.05  # Slight boost for extra time
        
        # Apply recovery boost if active
        recovery_boost = self.recovery_boost_active.get(student_id, 0.0)
        
        # Calculate final parameters
        final_slip = max(0.02, min(0.4, slip + stress_modifier + load_modifier + time_modifier - recovery_boost))
        final_guess = max(0.05, min(0.4, guess + stress_modifier * 0.5))  # Less impact on guess
        final_learn = max(0.1, min(0.6, adaptive_learn - load_modifier * 0.5 + recovery_boost))
        
        # BKT Update Equations
        pL = prior_mastery
        
        if correct:
            # P(L=1|correct) = P(correct|L=1) * P(L=1) / P(correct)
            numerator = pL * (1 - final_slip)
            denominator = pL * (1 - final_slip) + (1 - pL) * final_guess
        else:
            # P(L=1|incorrect) = P(incorrect|L=1) * P(L=1) / P(incorrect)  
            numerator = pL * final_slip
            denominator = pL * final_slip + (1 - pL) * (1 - final_guess)
        
        posterior = numerator / denominator if denominator > 1e-9 else pL
        
        # Learning transition: P(L=1 at t+1) = P(L=1 at t) + P(L=0 at t) * learn
        new_mastery = posterior + (1 - posterior) * final_learn
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        # Update concept tracker
        self.concept_tracker.update_concept_mastery(concept, new_mastery)
        
        # Update student profile
        self.student_profiles.update_student_profile(student_id, correct, stress)
        
        # Recovery mechanism
        if not correct:
            struggle_count = self.student_struggle_count.get(student_id, 0) + 1
            self.student_struggle_count[student_id] = struggle_count
            
            if struggle_count >= 3:  # After 3 incorrect responses
                self.recovery_boost_active[student_id] = 0.15  # Activate recovery boost
                logger.debug(f"[ImprovedBKT] Recovery boost activated for {student_id}")
        else:
            # Reset struggle count on correct response
            self.student_struggle_count[student_id] = 0
            # Gradually reduce recovery boost
            if student_id in self.recovery_boost_active:
                self.recovery_boost_active[student_id] = max(0.0, self.recovery_boost_active[student_id] - 0.03)
        
        # Calculate confidence based on attempts
        confidence = self.concept_tracker.get_confidence_weight(concept)
        
        logger.debug(f"[ImprovedBKT] {concept}: {prior_mastery:.3f}→{new_mastery:.3f} "
                    f"(slip={final_slip:.3f}, guess={final_guess:.3f}, learn={final_learn:.3f}, "
                    f"conf={confidence:.3f}, recovery={recovery_boost:.3f})")
        
        return {
            "mastery": float(new_mastery),
            "confidence": float(confidence),
            "concept": concept,
            "parameters": {
                "slip": float(final_slip),
                "guess": float(final_guess),
                "learn": float(final_learn)
            },
            "context_impact": {
                "stress_modifier": float(stress_modifier),
                "load_modifier": float(load_modifier),  
                "time_modifier": float(time_modifier),
                "recovery_boost": float(recovery_boost)
            }
        }
    
    def get_concept_mastery(self, concept: str) -> float:
        """Get current mastery for a specific concept"""
        return self.concept_tracker.get_concept_prior(concept)
    
    def get_all_masteries(self) -> Dict[str, float]:
        """Get all concept masteries"""
        return self.concept_tracker.concept_masteries.copy()
    
    def get_student_profile_summary(self, student_id: str) -> Dict[str, Any]:
        """Get student's adaptive profile summary"""
        return {
            "learning_rate": self.student_profiles.learning_rates.get(student_id, self.base_learn),
            "stress_tolerance": self.student_profiles.stress_tolerance.get(student_id, 0.5),
            "recent_performance": self.student_profiles.performance_history.get(student_id, [])[-5:],
            "recovery_active": self.recovery_boost_active.get(student_id, 0.0) > 0.01
        }