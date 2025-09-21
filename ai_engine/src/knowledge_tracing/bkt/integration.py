# ai_engine/src/knowledge_tracing/bkt/integration.py
import logging
from typing import Dict, Any, Optional
from ..recovery.intervention_manager import InterventionManager, InterventionResult
from .model import BayesianKnowledgeTracing

logger = logging.getLogger("bkt_integration")

class BKTInterventionIntegration:
    """
    Integrates the BKT system with the intervention manager to detect and respond to
    performance decline during learning sessions.
    """
    
    def __init__(self):
        self.intervention_manager = InterventionManager()
        self.student_topic_data: Dict[str, Dict[str, Any]] = {}
        
    async def process_response(self, 
                              student_id: str, 
                              concept_id: str, 
                              is_correct: bool, 
                              response_time_ms: Optional[int],
                              bkt_model: Any,
                              bkt_result: Dict[str, Any],
                              question_difficulty: float = 0.5,
                              time_pressure: float = 0.0) -> Optional[InterventionResult]:
        """
        Process a student response and check if intervention is needed
        
        Args:
            student_id: Student identifier
            concept_id: Concept/topic identifier
            is_correct: Whether the answer was correct
            response_time_ms: Response time in milliseconds
            bkt_model: BKT model instance
            bkt_result: Result from BKT update
            question_difficulty: Difficulty level of the question (0-1)
            time_pressure: Time pressure factor (0-1)
            
        Returns:
            InterventionResult if intervention is needed, None otherwise
        """
        # Calculate fatigue based on session length and response patterns
        rt_ms = response_time_ms or 0
        fatigue = self._estimate_fatigue(student_id, concept_id, rt_ms)
        
        # Add performance data to intervention manager
        self.intervention_manager.add_performance_data(
            student_id=student_id,
            topic=concept_id,
            is_correct=is_correct,
            response_time=rt_ms / 1000,  # Convert to seconds
            difficulty=question_difficulty,
            mastery_before=bkt_result.get("previous_mastery", 0.0),
            mastery_after=bkt_result.get("new_mastery", 0.0),
            time_pressure=time_pressure,
            fatigue=fatigue
        )
        
        # Check if intervention is needed
        intervention = self.intervention_manager.get_intervention(student_id, concept_id)
        
        if intervention:
            logger.info(f"Intervention triggered for student {student_id} on topic {concept_id}: "
                       f"{intervention.strategy_applied.name}")
            
        return intervention
    
    def _estimate_fatigue(self, student_id: str, concept_id: str, response_time_ms: Optional[int]) -> float:
        """
        Estimate student fatigue based on session length and response patterns
        
        Args:
            student_id: Student identifier
            concept_id: Concept/topic identifier
            response_time_ms: Response time in milliseconds
            
        Returns:
            Fatigue level (0-1)
        """
        key = f"{student_id}_{concept_id}"
        
        if key not in self.student_topic_data:
            self.student_topic_data[key] = {
                "session_start": None,
                "question_count": 0,
                "avg_response_time": 0,
                "response_times": []
            }
            
        data = self.student_topic_data[key]
        data["question_count"] += 1
        
        # Normalize None to 0 for calculations
        rt_ms = response_time_ms or 0
        
        # Track response times (keep last 10)
        data["response_times"].append(rt_ms)
        if len(data["response_times"]) > 10:
            data["response_times"].pop(0)
            
        # Calculate average response time
        data["avg_response_time"] = sum(data["response_times"]) / len(data["response_times"])
        
        # Calculate fatigue based on:
        # 1. Increasing response times compared to average
        # 2. Number of questions attempted in session
        
        # Response time factor (0-0.5): how much current response time exceeds average
        rt_factor = min(0.5, max(0, (rt_ms - data["avg_response_time"]) 
                                / (data["avg_response_time"] * 2 if data["avg_response_time"] else 1)))
        
        # Question count factor (0-0.5): increases with more questions
        question_factor = min(0.5, data["question_count"] / 20)
        
        # Combined fatigue estimate
        fatigue = rt_factor + question_factor
        
        return fatigue
        
    def reset_session(self, student_id: str, concept_id: str) -> None:
        """
        Reset session data for a student-topic pair
        
        Args:
            student_id: Student identifier
            concept_id: Concept/topic identifier
        """
        key = f"{student_id}_{concept_id}"
        if key in self.student_topic_data:
            self.student_topic_data[key]["session_start"] = None
            self.student_topic_data[key]["question_count"] = 0