# Enhanced Repository Layer for BKT Engine
# Based on proven knowledge_tracing repository architecture with advanced features

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, timedelta
import json
import logging
import asyncio
from collections import defaultdict, deque
from dataclasses import asdict
import statistics

from .enhanced_schemas import (
    BKTInteractionRecord, BKTEvaluationRecord, EnhancedTraceResponse,
    BKTEvaluationResponse, StudentProfileResponse, SystemAnalyticsResponse,
    ConceptMasteryDetail, InterventionData, ExamType
)
from .enhanced_multi_concept_bkt import StudentProfile, ConceptMastery

logger = logging.getLogger(__name__)

class AbstractBKTRepository(ABC):
    """Abstract base class for BKT data repositories"""
    
    @abstractmethod
    async def store_interaction(self, interaction: BKTInteractionRecord) -> str:
        """Store a BKT interaction record and return its ID"""
        pass
    
    @abstractmethod
    async def get_student_interactions(
        self, 
        student_id: str, 
        concept_id: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None
    ) -> List[BKTInteractionRecord]:
        """Get interaction history for a student"""
        pass
    
    @abstractmethod
    async def store_evaluation(self, evaluation: BKTEvaluationRecord) -> str:
        """Store evaluation results and return record ID"""
        pass
    
    @abstractmethod
    async def get_latest_evaluation(self, concept_id: Optional[str] = None) -> Optional[BKTEvaluationRecord]:
        """Get most recent evaluation results"""
        pass
    
    @abstractmethod
    async def store_student_profile(self, student_id: str, profile: StudentProfile) -> None:
        """Store updated student profile"""
        pass
    
    @abstractmethod
    async def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Retrieve student profile"""
        pass
    
    @abstractmethod
    async def get_concept_statistics(self, concept_id: str) -> Dict[str, Any]:
        """Get aggregated statistics for a concept"""
        pass
    
    @abstractmethod
    async def get_system_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system-wide health and performance metrics"""
        pass

class InMemoryBKTRepository(AbstractBKTRepository):
    """In-memory implementation for development and testing"""
    
    def __init__(self):
        self.interactions: List[BKTInteractionRecord] = []
        self.evaluations: List[BKTEvaluationRecord] = []
        self.student_profiles: Dict[str, StudentProfile] = {}
        self.concept_stats_cache: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {}
        self._id_counter = 0
        
    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"bkt_{self._id_counter:06d}"
    
    async def store_interaction(self, interaction: BKTInteractionRecord) -> str:
        """Store interaction record"""
        if not interaction.id:
            interaction.id = self._generate_id()
        self.interactions.append(interaction)
        
        # Update concept stats cache
        await self._update_concept_stats(interaction.concept_id)
        
        logger.debug(f"Stored interaction {interaction.id} for student {interaction.student_id}")
        return interaction.id
    
    async def get_student_interactions(
        self, 
        student_id: str, 
        concept_id: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None
    ) -> List[BKTInteractionRecord]:
        """Retrieve student interaction history"""
        interactions = [
            i for i in self.interactions 
            if i.student_id == student_id
        ]
        
        if concept_id:
            interactions = [i for i in interactions if i.concept_id == concept_id]
        
        if start_time:
            interactions = [i for i in interactions if i.timestamp >= start_time]
        
        # Sort by timestamp descending
        interactions.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            interactions = interactions[:limit]
        
        return interactions
    
    async def store_evaluation(self, evaluation: BKTEvaluationRecord) -> str:
        """Store evaluation results"""
        if not evaluation.id:
            evaluation.id = self._generate_id()
        self.evaluations.append(evaluation)
        
        logger.info(f"Stored evaluation {evaluation.id} with accuracy {evaluation.next_step_accuracy:.3f}")
        return evaluation.id
    
    async def get_latest_evaluation(self, concept_id: Optional[str] = None) -> Optional[BKTEvaluationRecord]:
        """Get most recent evaluation"""
        evaluations = self.evaluations
        
        if concept_id:
            evaluations = [e for e in evaluations if e.concept_filter == concept_id]
        
        if not evaluations:
            return None
        
        return max(evaluations, key=lambda x: x.evaluation_timestamp)
    
    async def store_student_profile(self, student_id: str, profile: StudentProfile) -> None:
        """Store student profile"""
        self.student_profiles[student_id] = profile
        logger.debug(f"Updated profile for student {student_id}")
    
    async def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile"""
        return self.student_profiles.get(student_id)
    
    async def get_concept_statistics(self, concept_id: str) -> Dict[str, Any]:
        """Get concept aggregated statistics"""
        if concept_id in self.concept_stats_cache:
            return self.concept_stats_cache[concept_id]
        
        return await self._calculate_concept_stats(concept_id)
    
    async def get_system_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system health metrics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_interactions = [
            i for i in self.interactions 
            if i.timestamp >= cutoff_time
        ]
        
        if not recent_interactions:
            return {
                "total_interactions": 0,
                "unique_students": 0,
                "unique_concepts": 0,
                "average_accuracy": 0.0,
                "throughput_per_hour": 0.0
            }
        
        unique_students = len(set(i.student_id for i in recent_interactions))
        unique_concepts = len(set(i.concept_id for i in recent_interactions))
        
        correct_predictions = sum(
            1 for i in recent_interactions 
            if abs(i.new_mastery - (1.0 if i.is_correct else 0.0)) < 0.5
        )
        
        return {
            "total_interactions": len(recent_interactions),
            "unique_students": unique_students,
            "unique_concepts": unique_concepts,
            "average_accuracy": correct_predictions / len(recent_interactions),
            "throughput_per_hour": len(recent_interactions) / hours,
            "average_processing_time": statistics.mean(
                i.processing_time_ms or 0 for i in recent_interactions
            )
        }
    
    async def _update_concept_stats(self, concept_id: str):
        """Update cached concept statistics"""
        stats = await self._calculate_concept_stats(concept_id)
        self.concept_stats_cache[concept_id] = stats
    
    async def _calculate_concept_stats(self, concept_id: str) -> Dict[str, Any]:
        """Calculate concept statistics from interactions"""
        concept_interactions = [
            i for i in self.interactions 
            if i.concept_id == concept_id
        ]
        
        if not concept_interactions:
            return {
                "total_interactions": 0,
                "unique_students": 0,
                "average_mastery": 0.0,
                "success_rate": 0.0
            }
        
        unique_students = len(set(i.student_id for i in concept_interactions))
        average_mastery = statistics.mean(i.new_mastery for i in concept_interactions)
        success_rate = sum(i.is_correct for i in concept_interactions) / len(concept_interactions)
        
        return {
            "total_interactions": len(concept_interactions),
            "unique_students": unique_students,
            "average_mastery": average_mastery,
            "success_rate": success_rate,
            "last_interaction": max(i.timestamp for i in concept_interactions).isoformat()
        }

class EnhancedBKTAnalyticsEngine:
    """Enhanced analytics engine for BKT system matching proven metrics"""
    
    def __init__(self, repository: AbstractBKTRepository):
        self.repository = repository
        self.prediction_history: deque = deque(maxlen=10000)  # Store recent predictions for evaluation
        self.accuracy_tracker = AccuracyTracker()
        
    async def compute_evaluation_metrics(
        self,
        concept_id: Optional[str] = None,
        student_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_interactions: int = 10
    ) -> BKTEvaluationResponse:
        """Compute comprehensive evaluation metrics matching proven system"""
        
        # Gather interaction data
        if student_id:
            interactions = await self.repository.get_student_interactions(
                student_id=student_id,
                concept_id=concept_id,
                start_time=start_time
            )
        else:
            # For system-wide evaluation, we'd need a different method
            # This is a simplified version
            interactions = []
        
        if len(interactions) < min_interactions:
            logger.warning(f"Insufficient interactions ({len(interactions)}) for reliable evaluation")
        
        # Calculate next-step prediction metrics (core validation from proven system)
        next_step_auc, next_step_accuracy = await self._calculate_next_step_metrics(interactions)
        
        # Calculate calibration metrics
        brier_score = await self._calculate_brier_score(interactions)
        calibration_error = await self._calculate_calibration_error(interactions)
        
        # Calculate trajectory analysis
        trajectory_validity = await self._calculate_trajectory_validity(interactions)
        mastery_progression_score = await self._calculate_mastery_progression(interactions)
        
        # Additional proven metrics
        knowledge_retention_score = await self._calculate_retention_score(interactions)
        transfer_learning_effectiveness = await self._calculate_transfer_effectiveness(interactions)
        adaptive_parameter_stability = await self._calculate_parameter_stability(interactions)
        
        # System performance metrics
        convergence_rate = await self._calculate_convergence_rate(interactions)
        prediction_variance = await self._calculate_prediction_variance(interactions)
        
        # Overall quality assessment
        overall_quality_score = self._compute_overall_quality_score({
            "next_step_auc": next_step_auc,
            "next_step_accuracy": next_step_accuracy,
            "brier_score": brier_score,
            "calibration_error": calibration_error,
            "trajectory_validity": trajectory_validity
        })
        
        recommendation = self._generate_recommendation(overall_quality_score)
        
        return BKTEvaluationResponse(
            next_step_auc=next_step_auc,
            next_step_accuracy=next_step_accuracy,
            brier_score=brier_score,
            calibration_error=calibration_error,
            trajectory_validity=trajectory_validity,
            mastery_progression_score=mastery_progression_score,
            knowledge_retention_score=knowledge_retention_score,
            transfer_learning_effectiveness=transfer_learning_effectiveness,
            adaptive_parameter_stability=adaptive_parameter_stability,
            convergence_rate=convergence_rate,
            prediction_variance=prediction_variance,
            recommendation=recommendation,
            overall_quality_score=overall_quality_score,
            evaluation_period=f"{start_time} to {end_time}" if start_time and end_time else "All time",
            total_interactions=len(interactions),
            total_students=len(set(i.student_id for i in interactions)) if interactions else 0,
            total_concepts=len(set(i.concept_id for i in interactions)) if interactions else 0
        )
    
    async def generate_student_profile(self, student_id: str) -> StudentProfileResponse:
        """Generate comprehensive student profile"""
        
        # Get student data
        profile = await self.repository.get_student_profile(student_id)
        interactions = await self.repository.get_student_interactions(student_id, limit=1000)
        
        if not profile:
            logger.warning(f"No profile found for student {student_id}")
            # Create minimal profile
            profile = StudentProfile(
                student_id=student_id,
                learning_rates={},
                stress_tolerance_levels={'general': 0.5},
                recovery_patterns={},
                performance_history=[],
                concept_masteries={}
            )
        
        # Calculate comprehensive analytics
        overall_performance = await self._calculate_overall_performance(interactions)
        learning_velocity = await self._calculate_learning_velocity(interactions)
        retention_strength = await self._calculate_retention_strength(interactions)
        stress_resilience = await self._calculate_stress_resilience(interactions)
        cognitive_load_tolerance = await self._calculate_cognitive_load_tolerance(interactions)
        
        # Concept mastery details
        concept_masteries = {}
        for concept_id, mastery in profile.concept_masteries.items():
            concept_interactions = [i for i in interactions if i.concept_id == concept_id]
            concept_masteries[concept_id] = ConceptMasteryDetail(
                concept_id=concept_id,
                mastery_probability=mastery.mastery_probability,
                confidence_level=mastery.confidence_level,
                practice_count=mastery.practice_count,
                consecutive_errors=mastery.consecutive_errors,
                last_interaction=max((i.timestamp for i in concept_interactions), default=datetime.now()),
                recent_performance=[i.is_correct for i in concept_interactions[-10:]],
                learning_rate=mastery.learning_rate,
                difficulty_comfort_zone=(0.3, 0.7),  # Default range
                predicted_exam_performance=mastery.mastery_probability * 0.9  # Conservative estimate
            )
        
        # Generate recommendations
        focus_recommendations = await self._generate_focus_recommendations(profile, interactions)
        study_strategy_recommendations = await self._generate_study_strategy_recommendations(profile)
        intervention_recommendations = await self._generate_intervention_recommendations(profile, interactions)
        
        return StudentProfileResponse(
            student_id=student_id,
            profile_generated_at=datetime.now(),
            overall_performance=overall_performance,
            total_interactions=len(interactions),
            active_days=len(set(i.timestamp.date() for i in interactions)),
            learning_velocity=learning_velocity,
            retention_strength=retention_strength,
            stress_resilience=stress_resilience,
            cognitive_load_tolerance=cognitive_load_tolerance,
            preferred_difficulty_level=0.5,  # TODO: Calculate from interaction patterns
            optimal_session_length=45,  # TODO: Calculate from session data
            best_time_of_day=None,  # TODO: Analyze time patterns
            concept_masteries=concept_masteries,
            subject_strengths={},  # TODO: Group concepts by subject
            subject_improvement_potential={},  # TODO: Calculate improvement potential
            exam_readiness_score=overall_performance,
            predicted_exam_performance={},  # TODO: Subject-wise predictions
            focus_recommendations=focus_recommendations,
            study_strategy_recommendations=study_strategy_recommendations,
            dropout_risk=max(0.0, 0.5 - overall_performance),  # Simple heuristic
            burnout_indicators=[],  # TODO: Detect burnout patterns
            intervention_recommendations=intervention_recommendations
        )
    
    async def generate_system_analytics(self, time_window_days: int = 7) -> SystemAnalyticsResponse:
        """Generate system-wide analytics"""
        
        health_metrics = await self.repository.get_system_health_metrics(time_window_days * 24)
        
        return SystemAnalyticsResponse(
            system_overview=health_metrics,
            overall_prediction_accuracy=health_metrics.get("average_accuracy", 0.0),
            concept_accuracies={},  # TODO: Per-concept breakdown
            accuracy_trend=[],  # TODO: Time series data
            performance_distribution={},  # TODO: Student performance distribution
            engagement_metrics={},  # TODO: Engagement analysis
            learning_velocity_distribution={},  # TODO: Learning velocity stats
            throughput_metrics={
                "requests_per_hour": health_metrics.get("throughput_per_hour", 0.0),
                "average_latency_ms": health_metrics.get("average_processing_time", 0.0)
            },
            model_stability_indicators={},  # TODO: Model stability metrics
            error_rates={},  # TODO: Error tracking
            retention_rates={},  # TODO: Student retention
            improvement_rates={},  # TODO: Learning improvement rates
            satisfaction_indicators={},  # TODO: User satisfaction metrics
            system_health_score=min(1.0, health_metrics.get("average_accuracy", 0.0) * 1.2),
            key_insights=[
                f"Processing {health_metrics.get('total_interactions', 0)} interactions",
                f"Serving {health_metrics.get('unique_students', 0)} unique students",
                f"Tracking {health_metrics.get('unique_concepts', 0)} concepts"
            ],
            optimization_recommendations=[],  # TODO: Performance optimization suggestions
            scaling_recommendations=[]  # TODO: Scaling recommendations
        )
    
    # Helper methods for metric calculations (matching proven system algorithms)
    
    async def _calculate_next_step_metrics(self, interactions: List[BKTInteractionRecord]) -> Tuple[float, float]:
        """Calculate next-step prediction AUC and accuracy (core validation metric)"""
        if len(interactions) < 2:
            return 0.5, 0.5
        
        # For each interaction, use previous mastery to predict current outcome
        predictions = []
        actuals = []
        
        for i in range(1, len(interactions)):
            prev_interaction = interactions[i-1]
            curr_interaction = interactions[i]
            
            if prev_interaction.concept_id == curr_interaction.concept_id:
                predictions.append(prev_interaction.new_mastery)
                actuals.append(1.0 if curr_interaction.is_correct else 0.0)
        
        if not predictions:
            return 0.5, 0.5
        
        # Calculate accuracy
        binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
        accuracy = sum(bp == a for bp, a in zip(binary_predictions, actuals)) / len(predictions)
        
        # Calculate AUC (simplified)
        auc = self._calculate_auc(predictions, actuals)
        
        return auc, accuracy
    
    async def _calculate_brier_score(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate Brier reliability score"""
        if len(interactions) < 2:
            return 0.5
        
        brier_scores = []
        for i in range(1, len(interactions)):
            prev_interaction = interactions[i-1]
            curr_interaction = interactions[i]
            
            if prev_interaction.concept_id == curr_interaction.concept_id:
                predicted_prob = prev_interaction.new_mastery
                actual_outcome = 1.0 if curr_interaction.is_correct else 0.0
                brier_score = (predicted_prob - actual_outcome) ** 2
                brier_scores.append(brier_score)
        
        return statistics.mean(brier_scores) if brier_scores else 0.5
    
    async def _calculate_calibration_error(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate expected calibration error"""
        # Simplified implementation
        # Group predictions into bins and measure calibration
        return 0.1  # Placeholder
    
    async def _calculate_trajectory_validity(self, interactions: List[BKTInteractionRecord]) -> float:
        """Assess validity of learning trajectories"""
        if len(interactions) < 3:
            return 0.5
        
        # Check if mastery generally increases over time for correct responses
        concept_trajectories = defaultdict(list)
        
        for interaction in interactions:
            concept_trajectories[interaction.concept_id].append(
                (interaction.timestamp, interaction.new_mastery, interaction.is_correct)
            )
        
        valid_trajectories = 0
        total_trajectories = 0
        
        for concept_id, trajectory in concept_trajectories.items():
            if len(trajectory) < 3:
                continue
            
            trajectory.sort(key=lambda x: x[0])  # Sort by timestamp
            
            # Check if mastery increases after correct responses
            increases_after_correct = 0
            total_correct = 0
            
            for i in range(1, len(trajectory)):
                if trajectory[i-1][2]:  # Previous was correct
                    total_correct += 1
                    if trajectory[i][1] > trajectory[i-1][1]:  # Mastery increased
                        increases_after_correct += 1
            
            if total_correct > 0:
                trajectory_validity = increases_after_correct / total_correct
                valid_trajectories += trajectory_validity
                total_trajectories += 1
        
        return valid_trajectories / total_trajectories if total_trajectories > 0 else 0.5
    
    async def _calculate_mastery_progression(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate quality of mastery progression"""
        return 0.8  # Placeholder
    
    async def _calculate_retention_score(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate knowledge retention score"""
        return 0.75  # Placeholder
    
    async def _calculate_transfer_effectiveness(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate transfer learning effectiveness"""
        return 0.7  # Placeholder
    
    async def _calculate_parameter_stability(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate adaptive parameter stability"""
        return 0.85  # Placeholder
    
    async def _calculate_convergence_rate(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate how quickly mastery estimates converge"""
        return 0.15  # Placeholder (higher means faster convergence)
    
    async def _calculate_prediction_variance(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate variance in prediction accuracy"""
        return 0.05  # Placeholder
    
    def _calculate_auc(self, predictions: List[float], actuals: List[float]) -> float:
        """Calculate Area Under ROC Curve (simplified)"""
        if not predictions or not actuals:
            return 0.5
        
        # Sort by prediction probability
        paired = list(zip(predictions, actuals))
        paired.sort(key=lambda x: x[0], reverse=True)
        
        # Count positive and negative samples
        n_pos = sum(actuals)
        n_neg = len(actuals) - n_pos
        
        if n_pos == 0 or n_neg == 0:
            return 0.5
        
        # Calculate AUC using trapezoidal rule approximation
        tp = fp = 0
        auc = 0
        prev_fp_rate = 0
        
        for pred, actual in paired:
            if actual == 1:
                tp += 1
            else:
                fp += 1
                # Add area
                fp_rate = fp / n_neg
                tp_rate = tp / n_pos
                auc += (fp_rate - prev_fp_rate) * tp_rate
                prev_fp_rate = fp_rate
        
        return auc
    
    def _compute_overall_quality_score(self, metrics: Dict[str, float]) -> float:
        """Compute overall quality score from individual metrics"""
        weights = {
            "next_step_auc": 0.3,
            "next_step_accuracy": 0.25,
            "brier_score": -0.2,  # Lower is better
            "calibration_error": -0.15,  # Lower is better
            "trajectory_validity": 0.1
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric, value in metrics.items():
            if metric in weights:
                weight = weights[metric]
                if weight > 0:
                    score += weight * value
                else:
                    score += weight * (1 - value)  # Invert for "lower is better" metrics
                total_weight += abs(weight)
        
        return max(0.0, min(1.0, score / total_weight)) if total_weight > 0 else 0.5
    
    def _generate_recommendation(self, quality_score: float) -> str:
        """Generate system recommendation based on quality score"""
        if quality_score >= 0.85:
            return "EXCELLENT"
        elif quality_score >= 0.7:
            return "GOOD"
        elif quality_score >= 0.5:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    # Student profile helper methods
    
    async def _calculate_overall_performance(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate student's overall performance score"""
        if not interactions:
            return 0.0
        
        recent_interactions = interactions[-50:]  # Focus on recent performance
        success_rate = sum(i.is_correct for i in recent_interactions) / len(recent_interactions)
        
        # Weight by difficulty and recency
        weighted_score = 0.0
        total_weight = 0.0
        
        for i, interaction in enumerate(recent_interactions):
            recency_weight = (i + 1) / len(recent_interactions)  # More recent = higher weight
            difficulty = interaction.question_metadata.get('difficulty', 0.5)
            difficulty_multiplier = 1 + difficulty  # Harder questions worth more
            
            weight = recency_weight * difficulty_multiplier
            score = 1.0 if interaction.is_correct else 0.0
            
            weighted_score += weight * score
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else success_rate
    
    async def _calculate_learning_velocity(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate rate of learning (concepts mastered per day)"""
        if len(interactions) < 2:
            return 0.0
        
        # Calculate based on mastery improvements over time
        concept_first_mastery = {}
        for interaction in interactions:
            concept_id = interaction.concept_id
            if concept_id not in concept_first_mastery and interaction.new_mastery >= 0.8:
                concept_first_mastery[concept_id] = interaction.timestamp
        
        if len(concept_first_mastery) < 2:
            return 0.1
        
        # Calculate time span and concepts mastered
        first_mastery = min(concept_first_mastery.values())
        last_mastery = max(concept_first_mastery.values())
        time_span_days = (last_mastery - first_mastery).total_seconds() / (24 * 3600)
        
        if time_span_days <= 0:
            return 1.0
        
        return len(concept_first_mastery) / time_span_days
    
    async def _calculate_retention_strength(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate knowledge retention ability"""
        # Analyze performance on concepts after breaks
        return 0.7  # Placeholder
    
    async def _calculate_stress_resilience(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate performance under stress"""
        stressed_interactions = [
            i for i in interactions 
            if i.context_factors.get('stress_level', 0) > 0.5
        ]
        
        if not stressed_interactions:
            return 0.5
        
        stressed_success_rate = sum(i.is_correct for i in stressed_interactions) / len(stressed_interactions)
        return stressed_success_rate
    
    async def _calculate_cognitive_load_tolerance(self, interactions: List[BKTInteractionRecord]) -> float:
        """Calculate ability to handle complex questions"""
        complex_interactions = [
            i for i in interactions 
            if i.context_factors.get('cognitive_load', 0) > 0.6
        ]
        
        if not complex_interactions:
            return 0.5
        
        complex_success_rate = sum(i.is_correct for i in complex_interactions) / len(complex_interactions)
        return complex_success_rate
    
    async def _generate_focus_recommendations(
        self, 
        profile: StudentProfile, 
        interactions: List[BKTInteractionRecord]
    ) -> List[str]:
        """Generate focus recommendations for student"""
        recommendations = []
        
        # Find concepts with low mastery but high importance
        low_mastery_concepts = [
            concept_id for concept_id, mastery in profile.concept_masteries.items()
            if mastery.mastery_probability < 0.6
        ]
        
        if low_mastery_concepts:
            recommendations.append(f"Focus on strengthening: {', '.join(low_mastery_concepts[:3])}")
        
        # Find concepts with high error streaks
        error_streak_concepts = [
            concept_id for concept_id, mastery in profile.concept_masteries.items()
            if mastery.consecutive_errors >= 3
        ]
        
        if error_streak_concepts:
            recommendations.append(f"Review fundamentals for: {', '.join(error_streak_concepts[:2])}")
        
        return recommendations or ["Continue balanced practice across all concepts"]
    
    async def _generate_study_strategy_recommendations(self, profile: StudentProfile) -> List[str]:
        """Generate study strategy recommendations"""
        recommendations = []
        
        if profile.stress_tolerance < 0.4:
            recommendations.append("Practice stress management techniques during study sessions")
        
        if profile.learning_rate < 0.1:
            recommendations.append("Break down complex concepts into smaller, manageable parts")
        
        recommendations.append("Review previously mastered concepts periodically to maintain retention")
        
        return recommendations
    
    async def _generate_intervention_recommendations(
        self, 
        profile: StudentProfile, 
        interactions: List[BKTInteractionRecord]
    ) -> List[InterventionData]:
        """Generate intervention recommendations"""
        interventions = []
        
        # Check for concerning patterns
        recent_performance = [i.is_correct for i in interactions[-20:]]
        if recent_performance and sum(recent_performance) / len(recent_performance) < 0.3:
            interventions.append(InterventionData(
                strategy="immediate_support",
                level="MODERATE",
                recommendations=[
                    "Schedule one-on-one tutoring session",
                    "Review fundamental concepts",
                    "Reduce difficulty temporarily"
                ],
                success_probability=0.7,
                trigger_reason="Poor recent performance (< 30% success rate)",
                estimated_duration_minutes=30
            ))
        
        return interventions

class AccuracyTracker:
    """Track prediction accuracy over time"""
    
    def __init__(self):
        self.predictions = deque(maxlen=1000)
        self.rolling_accuracy = 0.0
        
    def add_prediction(self, predicted: float, actual: bool):
        """Add a prediction result"""
        self.predictions.append((predicted, actual))
        self._update_rolling_accuracy()
    
    def _update_rolling_accuracy(self):
        """Update rolling accuracy calculation"""
        if not self.predictions:
            self.rolling_accuracy = 0.0
            return
        
        correct = sum(
            1 for pred, actual in self.predictions
            if (pred > 0.5) == actual
        )
        self.rolling_accuracy = correct / len(self.predictions)
    
    def get_current_accuracy(self) -> float:
        """Get current rolling accuracy"""
        return self.rolling_accuracy