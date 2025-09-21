# ai_engine/src/knowledge_tracing/recovery/intervention_manager.py
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
import math
import time

logger = logging.getLogger("intervention_manager")

class InterventionLevel(Enum):
    NONE = 0
    MILD = 1
    MODERATE = 2
    STRONG = 3
    CRITICAL = 4

@dataclass
class PerformanceMetrics:
    """Metrics used to evaluate student performance and detect decline"""
    recent_accuracy: float  # Accuracy over recent questions (e.g., last 5-10)
    trend_slope: float  # Slope of performance trend (negative indicates decline)
    consecutive_failures: int  # Number of consecutive incorrect answers
    time_pressure_factor: float  # How much time pressure is affecting performance (0-1)
    fatigue_level: float  # Estimated fatigue level (0-1)
    mastery_delta: float  # Change in mastery level over recent period
    
@dataclass
class InterventionStrategy:
    """Defines an intervention strategy to recover from performance decline"""
    name: str
    description: str
    level: InterventionLevel
    actions: List[str]
    expected_impact: float  # Expected improvement in performance (0-1)
    
@dataclass
class InterventionResult:
    """Result of applying an intervention"""
    strategy_applied: InterventionStrategy
    timestamp: float
    metrics_before: PerformanceMetrics
    success_probability: float
    recommendations: List[str]

class PerformanceDeclineDetector:
    """Detects patterns of performance decline in student learning"""
    
    def __init__(self, 
                 window_size: int = 5, 
                 decline_threshold: float = -0.1,
                 consecutive_failures_threshold: int = 3):
        self.window_size = window_size
        self.decline_threshold = decline_threshold
        self.consecutive_failures_threshold = consecutive_failures_threshold
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def add_performance_data(self, 
                            student_id: str, 
                            topic: str, 
                            is_correct: bool, 
                            response_time: float,
                            difficulty: float,
                            mastery_before: float,
                            mastery_after: float,
                            time_pressure: float = 0.0,
                            fatigue: float = 0.0) -> None:
        """
        Add new performance data point for a student on a specific topic
        
        Args:
            student_id: Student identifier
            topic: Topic identifier
            is_correct: Whether the answer was correct
            response_time: Time taken to respond (seconds)
            difficulty: Question difficulty (0-1)
            mastery_before: Mastery level before the question
            mastery_after: Mastery level after the question
            time_pressure: Time pressure factor (0-1)
            fatigue: Fatigue level (0-1)
        """
        key = f"{student_id}_{topic}"
        
        if key not in self.performance_history:
            self.performance_history[key] = []
            
        self.performance_history[key].append({
            "timestamp": time.time(),
            "is_correct": is_correct,
            "response_time": response_time,
            "difficulty": difficulty,
            "mastery_before": mastery_before,
            "mastery_after": mastery_after,
            "time_pressure": time_pressure,
            "fatigue": fatigue
        })
        
        # Keep only the most recent window_size * 3 entries
        if len(self.performance_history[key]) > self.window_size * 3:
            self.performance_history[key] = self.performance_history[key][-self.window_size * 3:]
            
    def detect_decline(self, student_id: str, topic: str) -> Optional[PerformanceMetrics]:
        """
        Detect if a student is experiencing performance decline
        
        Args:
            student_id: Student identifier
            topic: Topic identifier
            
        Returns:
            PerformanceMetrics if decline is detected, None otherwise
        """
        key = f"{student_id}_{topic}"
        
        if key not in self.performance_history:
            return None
            
        history = self.performance_history[key]
        
        if len(history) < self.window_size:
            return None
            
        # Get recent history
        recent = history[-self.window_size:]
        
        # Calculate metrics
        recent_accuracy = sum(1 for item in recent if item["is_correct"]) / len(recent)
        
        # Calculate trend slope using simple linear regression
        y_values = [1 if item["is_correct"] else 0 for item in recent]
        x_values = list(range(len(recent)))
        
        # Simple linear regression for trend
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x*y for x, y in zip(x_values, y_values))
        sum_xx = sum(x*x for x in x_values)
        
        # Avoid division by zero
        if n * sum_xx - sum_x * sum_x == 0:
            trend_slope = 0
        else:
            trend_slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        
        # Count consecutive failures
        consecutive_failures = 0
        for item in reversed(recent):
            if not item["is_correct"]:
                consecutive_failures += 1
            else:
                break
                
        # Calculate average time pressure and fatigue
        time_pressure_factor = sum(item["time_pressure"] for item in recent) / len(recent)
        fatigue_level = sum(item["fatigue"] for item in recent) / len(recent)
        
        # Calculate mastery delta
        if len(recent) > 1:
            mastery_delta = recent[-1]["mastery_after"] - recent[0]["mastery_before"]
        else:
            mastery_delta = 0
            
        metrics = PerformanceMetrics(
            recent_accuracy=recent_accuracy,
            trend_slope=trend_slope,
            consecutive_failures=consecutive_failures,
            time_pressure_factor=time_pressure_factor,
            fatigue_level=fatigue_level,
            mastery_delta=mastery_delta
        )
        
        # Determine if decline is detected
        if (trend_slope <= self.decline_threshold or 
            consecutive_failures >= self.consecutive_failures_threshold or
            (mastery_delta < 0 and recent_accuracy < 0.3)):
            return metrics
            
        return None

class InterventionManager:
    """
    Manages interventions to recover from performance decline
    """
    
    def __init__(self):
        self.detector = PerformanceDeclineDetector()
        self.intervention_history: Dict[str, List[InterventionResult]] = {}
        self.strategies = self._initialize_strategies()
        self.cooldown_periods: Dict[str, float] = {}  # Key -> timestamp of last intervention
        self.cooldown_time = 300  # 5 minutes between interventions
        
    def _initialize_strategies(self) -> List[InterventionStrategy]:
        """Initialize available intervention strategies"""
        return [
            InterventionStrategy(
                name="break_suggestion",
                description="Suggest a short break to reduce fatigue",
                level=InterventionLevel.MILD,
                actions=["suggest_break", "reduce_difficulty_temporarily"],
                expected_impact=0.2
            ),
            InterventionStrategy(
                name="concept_review",
                description="Suggest reviewing foundational concepts",
                level=InterventionLevel.MODERATE,
                actions=["show_concept_summary", "provide_examples", "reduce_difficulty"],
                expected_impact=0.4
            ),
            InterventionStrategy(
                name="learning_path_adjustment",
                description="Adjust learning path to focus on prerequisites",
                level=InterventionLevel.STRONG,
                actions=["switch_to_prerequisites", "simplify_questions", "provide_detailed_explanations"],
                expected_impact=0.6
            ),
            InterventionStrategy(
                name="comprehensive_intervention",
                description="Comprehensive intervention with multiple strategies",
                level=InterventionLevel.CRITICAL,
                actions=["enforce_break", "reset_to_fundamentals", "provide_detailed_guidance", 
                         "reduce_time_pressure", "add_motivational_content"],
                expected_impact=0.8
            )
        ]
        
    def add_performance_data(self, 
                            student_id: str, 
                            topic: str, 
                            is_correct: bool, 
                            response_time: float,
                            difficulty: float,
                            mastery_before: float,
                            mastery_after: float,
                            time_pressure: float = 0.0,
                            fatigue: float = 0.0) -> None:
        """Add performance data to the detector"""
        self.detector.add_performance_data(
            student_id=student_id,
            topic=topic,
            is_correct=is_correct,
            response_time=response_time,
            difficulty=difficulty,
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            time_pressure=time_pressure,
            fatigue=fatigue
        )
        
    def get_intervention(self, student_id: str, topic: str) -> Optional[InterventionResult]:
        """
        Get appropriate intervention if performance decline is detected
        
        Args:
            student_id: Student identifier
            topic: Topic identifier
            
        Returns:
            InterventionResult if intervention is needed, None otherwise
        """
        key = f"{student_id}_{topic}"
        
        # Check cooldown period
        current_time = time.time()
        if key in self.cooldown_periods and current_time - self.cooldown_periods[key] < self.cooldown_time:
            # During cooldown, return the last intervention if available (idempotent behavior)
            history = self.intervention_history.get(key)
            return history[-1] if history else None
            
        # Detect decline
        metrics = self.detector.detect_decline(student_id, topic)
        if not metrics:
            return None
            
        # Select appropriate strategy based on metrics
        strategy = self._select_strategy(metrics)
        
        # Record intervention
        result = InterventionResult(
            strategy_applied=strategy,
            timestamp=current_time,
            metrics_before=metrics,
            success_probability=self._calculate_success_probability(metrics, strategy),
            recommendations=self._generate_recommendations(metrics, strategy)
        )
        
        if key not in self.intervention_history:
            self.intervention_history[key] = []
            
        self.intervention_history[key].append(result)
        self.cooldown_periods[key] = current_time
        
        return result
        
    def _select_strategy(self, metrics: PerformanceMetrics) -> InterventionStrategy:
        """Select appropriate intervention strategy based on metrics"""
        # Determine severity of decline
        severity_score = 0
        
        if metrics.consecutive_failures >= 5:
            severity_score += 3
        elif metrics.consecutive_failures >= 3:
            severity_score += 2
        if metrics.trend_slope <= -0.5:
            severity_score += 3
        elif metrics.trend_slope <= -0.35:
            severity_score += 2
        elif metrics.trend_slope <= -0.3:
            severity_score += 1
            
        if metrics.recent_accuracy <= 0.2:
            severity_score += 3
        elif metrics.recent_accuracy <= 0.35:
            severity_score += 2
        elif metrics.recent_accuracy <= 0.55:
            severity_score += 1
            
        if metrics.time_pressure_factor >= 0.85:
            severity_score += 2
        elif metrics.time_pressure_factor >= 0.5:
            severity_score += 1
            
        if metrics.fatigue_level >= 0.85:
            severity_score += 2
        elif metrics.fatigue_level >= 0.5:
            severity_score += 1
            
        # Select strategy based on severity (tuned to align with expected scenarios)
        if severity_score >= 9:
            level = InterventionLevel.CRITICAL
        elif severity_score >= 7:
            level = InterventionLevel.STRONG
        elif severity_score >= 4:
            level = InterventionLevel.MODERATE
        else:
            level = InterventionLevel.MILD
            
        # Find matching strategy
        for strategy in self.strategies:
            if strategy.level == level:
                return strategy
                
        # Fallback to mild intervention
        return next(s for s in self.strategies if s.level == InterventionLevel.MILD)
        
    def _calculate_success_probability(self, metrics: PerformanceMetrics, strategy: InterventionStrategy) -> float:
        """Calculate probability of intervention success"""
        # Base probability from strategy's expected impact
        base_prob = strategy.expected_impact
        
        # Adjust based on metrics
        adjustments = 0
        
        # More effective for high fatigue
        if strategy.name == "break_suggestion":
            adjustments += metrics.fatigue_level * 0.2
            
        # More effective for conceptual issues
        if strategy.name == "concept_review":
            adjustments += (1 - metrics.recent_accuracy) * 0.2
            
        # More effective for prerequisite issues
        if strategy.name == "learning_path_adjustment":
            adjustments += (metrics.consecutive_failures / 5) * 0.2
            
        # Comprehensive intervention works better for severe cases
        if strategy.name == "comprehensive_intervention":
            adjustments += (metrics.consecutive_failures / 5) * 0.1
            adjustments += (1 - metrics.recent_accuracy) * 0.1
            
        # Cap probability between 0.1 and 0.95
        return max(0.1, min(0.95, base_prob + adjustments))
        
    def _generate_recommendations(self, metrics: PerformanceMetrics, strategy: InterventionStrategy) -> List[str]:
        """Generate specific recommendations based on metrics and strategy"""
        recommendations = []
        
        if "suggest_break" in strategy.actions:
            if metrics.fatigue_level >= 0.7:
                recommendations.append("Take a 15-minute break to refresh your mind")
            else:
                recommendations.append("Consider a short 5-minute break")
                
        if "reduce_difficulty_temporarily" in strategy.actions:
            recommendations.append("Temporarily reducing question difficulty to build confidence")
            
        if "show_concept_summary" in strategy.actions:
            recommendations.append("Review the key concepts before continuing")
            
        if "provide_examples" in strategy.actions:
            recommendations.append("Examine worked examples to reinforce understanding")
            
        if "switch_to_prerequisites" in strategy.actions:
            recommendations.append("Focusing on prerequisite concepts to strengthen foundation")
            
        if "simplify_questions" in strategy.actions:
            recommendations.append("Simplifying questions to build mastery step by step")
            
        if "provide_detailed_explanations" in strategy.actions:
            recommendations.append("Providing detailed explanations for each step")
            
        if "enforce_break" in strategy.actions:
            recommendations.append("Taking a mandatory break to reset focus and reduce fatigue")
            
        if "reset_to_fundamentals" in strategy.actions:
            recommendations.append("Returning to fundamental concepts to rebuild knowledge")
            
        if "reduce_time_pressure" in strategy.actions:
            recommendations.append("Removing time limits to reduce pressure")
            
        if "add_motivational_content" in strategy.actions:
            recommendations.append("Adding motivational content to boost confidence")
            
        return recommendations