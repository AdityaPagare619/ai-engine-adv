# BKT Performance Evaluator - Analytics and Monitoring
# Evaluates BKT engine performance and provides detailed analytics

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import json
import logging
from collections import defaultdict
from .multi_concept_bkt import EnhancedMultiConceptBKT

@dataclass
class PerformanceMetrics:
    """Performance metrics for BKT evaluation"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    calibration_error: float
    convergence_rate: float
    transfer_effectiveness: float

@dataclass
class StudentAnalytics:
    """Analytics for individual student performance"""
    student_id: str
    total_interactions: int
    accuracy_trend: List[float]
    mastery_progression: Dict[str, List[float]]
    learning_velocity: float
    plateau_detection: bool
    intervention_needed: bool
    strengths: List[str]
    weaknesses: List[str]

class BKTPerformanceEvaluator:
    """
    Comprehensive performance evaluation system for BKT engine
    Provides detailed analytics, monitoring, and optimization insights
    """
    
    def __init__(self, bkt_engine: EnhancedMultiConceptBKT):
        self.bkt_engine = bkt_engine
        self.evaluation_history: List[Dict] = []
        self.student_analytics: Dict[str, StudentAnalytics] = {}
        self.performance_benchmarks: Dict[str, float] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Evaluation parameters
        self.min_interactions_for_eval = 10
        self.convergence_threshold = 0.02  # 2% change for convergence
        self.plateau_detection_window = 20  # Number of interactions to check for plateau
        self.calibration_bins = 10
        
        self._initialize_benchmarks()
    
    def _initialize_benchmarks(self):
        """Initialize performance benchmarks for comparison"""
        self.performance_benchmarks = {
            'accuracy': 0.75,  # 75% minimum accuracy
            'precision': 0.70,
            'recall': 0.70,
            'f1_score': 0.70,
            'calibration_error': 0.15,  # Maximum acceptable calibration error
            'convergence_rate': 0.80,  # 80% of students should converge
            'transfer_effectiveness': 0.25,  # 25% improvement from transfer learning
            'learning_velocity': 0.05,  # 5% mastery gain per 10 interactions
        }
    
    def evaluate_prediction_accuracy(self, time_window_hours: int = 24) -> Dict:
        """Evaluate BKT prediction accuracy over specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Get recent interactions from BKT performance log
        recent_interactions = [
            log for log in self.bkt_engine.performance_log
            if datetime.fromisoformat(log['timestamp']) > cutoff_time
        ]
        
        if len(recent_interactions) < self.min_interactions_for_eval:
            return {'error': f'Insufficient data. Need at least {self.min_interactions_for_eval} interactions.'}
        
        # Calculate prediction accuracy metrics
        correct_predictions = 0
        total_predictions = len(recent_interactions)
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        predicted_probs = []
        actual_results = []
        
        for interaction in recent_interactions:
            is_correct = interaction['is_correct']
            mastery = interaction['old_mastery']  # Use pre-update mastery for prediction
            
            # Simple prediction: if mastery > 0.5, predict correct
            predicted_correct = mastery > 0.5
            
            predicted_probs.append(mastery)
            actual_results.append(1 if is_correct else 0)
            
            if is_correct:
                if predicted_correct:
                    true_positives += 1
                    correct_predictions += 1
                else:
                    false_negatives += 1
            else:
                if not predicted_correct:
                    true_negatives += 1
                    correct_predictions += 1
                else:
                    false_positives += 1
        
        # Calculate metrics
        accuracy = correct_predictions / total_predictions
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Calculate AUC-ROC approximation
        auc_roc = self._calculate_auc_roc(predicted_probs, actual_results)
        
        # Calculate calibration error
        calibration_error = self._calculate_calibration_error(predicted_probs, actual_results)
        
        return {
            'time_window_hours': time_window_hours,
            'total_interactions': total_predictions,
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1_score, 4),
            'auc_roc': round(auc_roc, 4),
            'calibration_error': round(calibration_error, 4),
            'performance_grade': self._grade_performance('accuracy', accuracy),
            'meets_benchmark': accuracy >= self.performance_benchmarks['accuracy']
        }
    
    def _calculate_auc_roc(self, predicted_probs: List[float], actual_results: List[int]) -> float:
        """Calculate approximate AUC-ROC score"""
        if not predicted_probs or not actual_results:
            return 0.5
        
        # Simple approximation using trapezoidal rule
        thresholds = np.linspace(0, 1, 100)
        tpr_values = []
        fpr_values = []
        
        for threshold in thresholds:
            tp = fp = tn = fn = 0
            
            for prob, actual in zip(predicted_probs, actual_results):
                predicted = 1 if prob >= threshold else 0
                
                if actual == 1:
                    if predicted == 1:
                        tp += 1
                    else:
                        fn += 1
                else:
                    if predicted == 1:
                        fp += 1
                    else:
                        tn += 1
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            tpr_values.append(tpr)
            fpr_values.append(fpr)
        
        # Calculate AUC using trapezoidal rule
        auc = np.trapz(tpr_values, fpr_values)
        return abs(auc)  # Ensure positive value
    
    def _calculate_calibration_error(self, predicted_probs: List[float], actual_results: List[int]) -> float:
        """Calculate calibration error (reliability diagram)"""
        if not predicted_probs or not actual_results:
            return 0.0
        
        bins = np.linspace(0, 1, self.calibration_bins + 1)
        bin_boundaries = [(bins[i], bins[i+1]) for i in range(self.calibration_bins)]
        
        calibration_error = 0.0
        total_samples = len(predicted_probs)
        
        for lower, upper in bin_boundaries:
            # Find predictions in this bin
            in_bin = [(prob, actual) for prob, actual in zip(predicted_probs, actual_results)
                     if lower <= prob < upper or (upper == 1.0 and prob == 1.0)]
            
            if not in_bin:
                continue
            
            bin_size = len(in_bin)
            bin_accuracy = sum(actual for _, actual in in_bin) / bin_size
            bin_confidence = sum(prob for prob, _ in in_bin) / bin_size
            
            # Weight by bin size
            calibration_error += (bin_size / total_samples) * abs(bin_accuracy - bin_confidence)
        
        return calibration_error
    
    def analyze_student_learning_patterns(self, student_id: str) -> Dict:
        """Analyze detailed learning patterns for a specific student"""
        if student_id not in self.bkt_engine.student_masteries:
            return {'error': 'Student not found'}
        
        # Get student's interaction history
        student_interactions = [
            log for log in self.bkt_engine.performance_log
            if log['student_id'] == student_id
        ]
        
        if len(student_interactions) < self.min_interactions_for_eval:
            return {'error': 'Insufficient interaction data for analysis'}
        
        # Analyze mastery progression
        mastery_progression = defaultdict(list)
        accuracy_trend = []
        recent_window = student_interactions[-20:] if len(student_interactions) >= 20 else student_interactions
        
        for interaction in student_interactions:
            concept_id = interaction['concept_id']
            mastery_progression[concept_id].append({
                'timestamp': interaction['timestamp'],
                'mastery': interaction['new_mastery'],
                'is_correct': interaction['is_correct']
            })
        
        # Calculate accuracy trend (moving average)
        window_size = 5
        for i in range(len(student_interactions)):
            start_idx = max(0, i - window_size + 1)
            window_interactions = student_interactions[start_idx:i+1]
            window_accuracy = sum(1 for int_ in window_interactions if int_['is_correct']) / len(window_interactions)
            accuracy_trend.append(window_accuracy)
        
        # Calculate learning velocity (mastery gain rate)
        total_mastery_gains = sum(
            max(0, interaction['mastery_change']) 
            for interaction in student_interactions
        )
        learning_velocity = total_mastery_gains / len(student_interactions)
        
        # Detect learning plateau
        plateau_detected = self._detect_learning_plateau(student_interactions)
        
        # Identify strengths and weaknesses
        concept_performance = {}
        for concept_id, progression in mastery_progression.items():
            recent_mastery = progression[-1]['mastery'] if progression else 0
            concept_accuracy = sum(1 for p in progression if p['is_correct']) / len(progression)
            
            concept_performance[concept_id] = {
                'current_mastery': recent_mastery,
                'accuracy': concept_accuracy,
                'interactions': len(progression)
            }
        
        strengths = [concept for concept, perf in concept_performance.items() 
                    if perf['current_mastery'] > 0.8 and perf['accuracy'] > 0.7]
        weaknesses = [concept for concept, perf in concept_performance.items() 
                     if perf['current_mastery'] < 0.4 or perf['accuracy'] < 0.5]
        
        # Determine if intervention is needed
        intervention_needed = (
            learning_velocity < self.performance_benchmarks['learning_velocity'] or
            plateau_detected or
            len(weaknesses) > len(strengths) * 2
        )
        
        return {
            'student_id': student_id,
            'total_interactions': len(student_interactions),
            'learning_velocity': round(learning_velocity, 4),
            'current_accuracy': round(accuracy_trend[-1] if accuracy_trend else 0, 4),
            'accuracy_trend': [round(acc, 3) for acc in accuracy_trend[-10:]],  # Last 10 points
            'plateau_detected': plateau_detected,
            'intervention_needed': intervention_needed,
            'strengths': strengths[:5],  # Top 5 strengths
            'weaknesses': weaknesses[:5],  # Top 5 weaknesses
            'concept_performance': {
                concept: {
                    'mastery': round(perf['current_mastery'], 3),
                    'accuracy': round(perf['accuracy'], 3),
                    'interactions': perf['interactions']
                }
                for concept, perf in sorted(
                    concept_performance.items(), 
                    key=lambda x: x[1]['current_mastery'], 
                    reverse=True
                )[:10]  # Top 10 concepts by mastery
            },
            'recommendations': self._generate_student_recommendations(
                learning_velocity, plateau_detected, strengths, weaknesses
            )
        }
    
    def _detect_learning_plateau(self, interactions: List[Dict]) -> bool:
        """Detect if student has hit a learning plateau"""
        if len(interactions) < self.plateau_detection_window:
            return False
        
        recent_interactions = interactions[-self.plateau_detection_window:]
        mastery_changes = [interaction['mastery_change'] for interaction in recent_interactions]
        
        # Check if mastery changes are consistently small
        avg_change = np.mean(mastery_changes)
        std_change = np.std(mastery_changes)
        
        # Plateau if average change is small and variance is low
        return avg_change < self.convergence_threshold and std_change < self.convergence_threshold
    
    def _generate_student_recommendations(self, learning_velocity: float, plateau_detected: bool,
                                        strengths: List[str], weaknesses: List[str]) -> List[str]:
        """Generate personalized recommendations for student"""
        recommendations = []
        
        if learning_velocity < self.performance_benchmarks['learning_velocity']:
            recommendations.append("Consider adjusting study approach - current learning pace is below optimal")
        
        if plateau_detected:
            recommendations.append("Learning plateau detected - recommend changing study strategy or taking a break")
        
        if len(weaknesses) > len(strengths):
            recommendations.append(f"Focus on weak areas: {', '.join(weaknesses[:3])}")
        
        if len(strengths) > 3:
            recommendations.append(f"Leverage strong concepts for transfer learning: {', '.join(strengths[:3])}")
        
        if not recommendations:
            recommendations.append("Student is progressing well - maintain current study approach")
        
        return recommendations
    
    def _grade_performance(self, metric: str, value: float) -> str:
        """Grade performance based on benchmarks"""
        benchmark = self.performance_benchmarks.get(metric, 0.5)
        
        if value >= benchmark * 1.1:  # 10% above benchmark
            return "Excellent"
        elif value >= benchmark:
            return "Good"
        elif value >= benchmark * 0.8:  # Within 20% of benchmark
            return "Fair"
        else:
            return "Needs Improvement"
    
    def evaluate_transfer_learning_effectiveness(self) -> Dict:
        """Evaluate how effective transfer learning is in the system"""
        recent_interactions = self.bkt_engine.performance_log[-1000:]  # Last 1000 interactions
        
        if not recent_interactions:
            return {'error': 'No interaction data available'}
        
        # Separate interactions with and without transfer learning
        with_transfer = [log for log in recent_interactions if log.get('transfer_boost', 0) > 0]
        without_transfer = [log for log in recent_interactions if log.get('transfer_boost', 0) == 0]
        
        if not with_transfer or not without_transfer:
            return {'message': 'Insufficient data to compare transfer learning effectiveness'}
        
        # Calculate average mastery gains
        avg_gain_with_transfer = np.mean([log['mastery_change'] for log in with_transfer])
        avg_gain_without_transfer = np.mean([log['mastery_change'] for log in without_transfer])
        
        transfer_effectiveness = avg_gain_with_transfer - avg_gain_without_transfer
        improvement_percentage = (transfer_effectiveness / avg_gain_without_transfer) * 100 if avg_gain_without_transfer > 0 else 0
        
        # Calculate accuracy comparison
        accuracy_with_transfer = sum(1 for log in with_transfer if log['is_correct']) / len(with_transfer)
        accuracy_without_transfer = sum(1 for log in without_transfer if log['is_correct']) / len(without_transfer)
        
        return {
            'total_interactions': len(recent_interactions),
            'with_transfer_count': len(with_transfer),
            'without_transfer_count': len(without_transfer),
            'avg_mastery_gain_with_transfer': round(avg_gain_with_transfer, 4),
            'avg_mastery_gain_without_transfer': round(avg_gain_without_transfer, 4),
            'transfer_effectiveness': round(transfer_effectiveness, 4),
            'improvement_percentage': round(improvement_percentage, 2),
            'accuracy_with_transfer': round(accuracy_with_transfer, 4),
            'accuracy_without_transfer': round(accuracy_without_transfer, 4),
            'transfer_grade': self._grade_performance('transfer_effectiveness', transfer_effectiveness),
            'meets_benchmark': transfer_effectiveness >= self.performance_benchmarks['transfer_effectiveness']
        }
    
    def generate_comprehensive_report(self, include_student_details: bool = False) -> Dict:
        """Generate comprehensive BKT performance report"""
        try:
            # Overall system metrics
            prediction_accuracy = self.evaluate_prediction_accuracy(time_window_hours=168)  # 1 week
            transfer_effectiveness = self.evaluate_transfer_learning_effectiveness()
            
            # Student population analysis
            total_students = len(self.bkt_engine.student_masteries)
            active_students = len([
                sid for sid in self.bkt_engine.student_masteries.keys()
                if any(log['student_id'] == sid for log in self.bkt_engine.performance_log[-500:])
            ])
            
            # Concept coverage analysis
            concept_stats = defaultdict(lambda: {'interactions': 0, 'avg_mastery': 0, 'students': set()})
            for log in self.bkt_engine.performance_log[-1000:]:
                concept_id = log['concept_id']
                student_id = log['student_id']
                concept_stats[concept_id]['interactions'] += 1
                concept_stats[concept_id]['students'].add(student_id)
            
            # Calculate average mastery per concept
            for concept_id in concept_stats:
                concept_masteries = []
                for student_id, masteries in self.bkt_engine.student_masteries.items():
                    if concept_id in masteries:
                        concept_masteries.append(masteries[concept_id].mastery_probability)
                
                concept_stats[concept_id]['avg_mastery'] = np.mean(concept_masteries) if concept_masteries else 0
                concept_stats[concept_id]['students'] = len(concept_stats[concept_id]['students'])
            
            # Top performing concepts
            top_concepts = sorted(
                concept_stats.items(),
                key=lambda x: (x[1]['avg_mastery'], x[1]['interactions']),
                reverse=True
            )[:5]
            
            # Struggling concepts
            struggling_concepts = sorted(
                concept_stats.items(),
                key=lambda x: (x[1]['avg_mastery'], -x[1]['interactions'])
            )[:5]
            
            # Student analysis summary
            student_summaries = []
            if include_student_details:
                for student_id in list(self.bkt_engine.student_masteries.keys())[:10]:  # Top 10 students
                    student_analysis = self.analyze_student_learning_patterns(student_id)
                    if 'error' not in student_analysis:
                        student_summaries.append(student_analysis)
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'system_overview': {
                    'total_students': total_students,
                    'active_students': active_students,
                    'total_concepts_covered': len(concept_stats),
                    'total_interactions_analyzed': len(self.bkt_engine.performance_log),
                    'engine_health': self.bkt_engine.get_performance_summary().get('engine_health', 'unknown')
                },
                'prediction_performance': prediction_accuracy,
                'transfer_learning': transfer_effectiveness,
                'concept_analysis': {
                    'top_performing': [
                        {
                            'concept': concept,
                            'avg_mastery': round(stats['avg_mastery'], 3),
                            'interactions': stats['interactions'],
                            'students': stats['students']
                        }
                        for concept, stats in top_concepts
                    ],
                    'struggling_areas': [
                        {
                            'concept': concept,
                            'avg_mastery': round(stats['avg_mastery'], 3),
                            'interactions': stats['interactions'],
                            'students': stats['students']
                        }
                        for concept, stats in struggling_concepts
                    ]
                },
                'recommendations': self._generate_system_recommendations(
                    prediction_accuracy, transfer_effectiveness, concept_stats
                ),
                'benchmarks_status': {
                    'accuracy_benchmark': prediction_accuracy.get('meets_benchmark', False),
                    'transfer_benchmark': transfer_effectiveness.get('meets_benchmark', False),
                    'overall_grade': self._calculate_overall_grade(prediction_accuracy, transfer_effectiveness)
                }
            }
            
            if include_student_details:
                report['student_details'] = student_summaries
            
            # Store report in evaluation history
            self.evaluation_history.append({
                'timestamp': datetime.now().isoformat(),
                'report_summary': {
                    'accuracy': prediction_accuracy.get('accuracy', 0),
                    'transfer_effectiveness': transfer_effectiveness.get('transfer_effectiveness', 0),
                    'total_students': total_students,
                    'active_students': active_students
                }
            })
            
            # Keep only last 50 evaluation reports
            if len(self.evaluation_history) > 50:
                self.evaluation_history = self.evaluation_history[-50:]
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return {'error': f'Report generation failed: {str(e)}'}
    
    def _generate_system_recommendations(self, prediction_accuracy: Dict, 
                                       transfer_effectiveness: Dict, 
                                       concept_stats: Dict) -> List[str]:
        """Generate system-wide recommendations"""
        recommendations = []
        
        accuracy = prediction_accuracy.get('accuracy', 0)
        if accuracy < self.performance_benchmarks['accuracy']:
            recommendations.append(f"System accuracy ({accuracy:.3f}) below benchmark - consider parameter tuning")
        
        transfer_eff = transfer_effectiveness.get('transfer_effectiveness', 0)
        if transfer_eff < self.performance_benchmarks['transfer_effectiveness']:
            recommendations.append("Transfer learning effectiveness is low - review concept relationships")
        
        # Check for concept coverage issues
        low_interaction_concepts = [
            concept for concept, stats in concept_stats.items()
            if stats['interactions'] < 10
        ]
        
        if len(low_interaction_concepts) > 5:
            recommendations.append(f"Limited interaction data for {len(low_interaction_concepts)} concepts - consider content review")
        
        # Check for mastery distribution
        avg_masteries = [stats['avg_mastery'] for stats in concept_stats.values()]
        if avg_masteries:
            overall_avg = np.mean(avg_masteries)
            if overall_avg < 0.6:
                recommendations.append("Overall mastery levels are low - consider difficulty adjustment")
        
        if not recommendations:
            recommendations.append("System performance is meeting benchmarks - continue monitoring")
        
        return recommendations
    
    def _calculate_overall_grade(self, prediction_accuracy: Dict, transfer_effectiveness: Dict) -> str:
        """Calculate overall system grade"""
        accuracy = prediction_accuracy.get('accuracy', 0)
        transfer_eff = transfer_effectiveness.get('transfer_effectiveness', 0)
        
        # Weight accuracy more heavily
        composite_score = (accuracy * 0.7) + (min(transfer_eff, 0.3) * 0.3 / 0.3)
        
        if composite_score >= 0.85:
            return "Excellent"
        elif composite_score >= 0.75:
            return "Good"
        elif composite_score >= 0.65:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def export_evaluation_data(self) -> Dict:
        """Export evaluation data for external analysis"""
        return {
            'evaluation_history': self.evaluation_history,
            'performance_benchmarks': self.performance_benchmarks,
            'system_parameters': {
                'min_interactions_for_eval': self.min_interactions_for_eval,
                'convergence_threshold': self.convergence_threshold,
                'plateau_detection_window': self.plateau_detection_window,
                'calibration_bins': self.calibration_bins
            },
            'export_timestamp': datetime.now().isoformat()
        }