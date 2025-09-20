# ai_engine/src/knowledge_tracing/fairness/advanced_fairness_monitor.py
"""
Advanced Fairness Monitoring System with Real-time Bias Detection and Correction
Implements comprehensive fairness metrics as outlined in the Blueprint
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy import stats
from sklearn.metrics import confusion_matrix
import warnings

logger = logging.getLogger("advanced_fairness")

@dataclass
class StudentDemographics:
    """Comprehensive student demographic and ability profile"""
    student_id: str
    reading_ability_level: float  # 0.0 (low) to 1.0 (high)
    language_proficiency: float   # 0.0 (ESL beginner) to 1.0 (native)
    socioeconomic_status: str     # "low", "medium", "high"
    prior_education_quality: float  # 0.0 (poor) to 1.0 (excellent)
    learning_disability_status: bool
    gender: str  # "male", "female", "non_binary", "prefer_not_to_say"
    ethnicity: str
    age_group: str  # "13-15", "16-18", "19-21", etc.
    device_quality: str  # "low_end", "medium", "high_end"
    internet_stability: float  # 0.0 (poor) to 1.0 (excellent)

@dataclass
class FairnessMetrics:
    """Comprehensive fairness evaluation metrics"""
    demographic_parity: float
    equalized_odds: float
    equality_of_opportunity: float
    calibration_parity: float
    individual_fairness_score: float
    counterfactual_fairness: float
    reading_ability_parity: float
    language_proficiency_parity: float

@dataclass
class BiasAlert:
    """Bias detection alert with remediation suggestions"""
    alert_id: str
    timestamp: datetime
    bias_type: str
    affected_groups: List[str]
    severity_level: str  # "low", "medium", "high", "critical"
    metric_values: Dict[str, float]
    suggested_actions: List[str]
    confidence_level: float

class AdvancedFairnessMonitor:
    """
    Advanced fairness monitoring system with real-time bias detection,
    correction mechanisms, and comprehensive demographic analysis
    """
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.alert_thresholds = alert_thresholds or {
            'demographic_parity': 0.1,
            'equalized_odds': 0.1, 
            'calibration_parity': 0.15,
            'reading_ability_parity': 0.12,
            'language_proficiency_parity': 0.15
        }
        
        # Storage for analysis
        self.student_profiles: Dict[str, StudentDemographics] = {}
        self.prediction_history: List[Dict[str, Any]] = []
        self.bias_alerts: List[BiasAlert] = []
        
        # Bias correction parameters
        self.bias_correctors = {}
        self.calibration_models = {}
        
    def register_student(self, demographics: StudentDemographics):
        """Register student demographic and ability profile"""
        self.student_profiles[demographics.student_id] = demographics
        logger.info(f"Registered student {demographics.student_id} for fairness monitoring")
        
    def record_prediction(self, student_id: str, topic: str, 
                         predicted_mastery: float, actual_outcome: bool,
                         question_difficulty: float, response_time_ms: float):
        """Record prediction for fairness analysis"""
        if student_id not in self.student_profiles:
            logger.warning(f"Student {student_id} not registered for fairness monitoring")
            return
            
        record = {
            'timestamp': datetime.now(),
            'student_id': student_id,
            'topic': topic,
            'predicted_mastery': predicted_mastery,
            'actual_outcome': actual_outcome,
            'question_difficulty': question_difficulty,
            'response_time_ms': response_time_ms,
            'demographics': self.student_profiles[student_id]
        }
        
        self.prediction_history.append(record)
        
        # Real-time bias check if we have enough data
        if len(self.prediction_history) % 100 == 0:  # Check every 100 predictions
            self._perform_real_time_bias_check()
    
    def compute_demographic_parity(self, group_predictions: Dict[str, List[float]]) -> Tuple[float, Dict[str, float]]:
        """
        Compute demographic parity: P(Y_hat = 1 | A = a) should be similar across groups
        """
        group_rates = {}
        for group, predictions in group_predictions.items():
            if predictions:
                positive_rate = np.mean([p > 0.5 for p in predictions])
                group_rates[group] = positive_rate
        
        if len(group_rates) < 2:
            return 0.0, group_rates
            
        rates = list(group_rates.values())
        parity_violation = max(rates) - min(rates)
        
        return parity_violation, group_rates
    
    def compute_equalized_odds(self, group_data: Dict[str, Dict[str, List]]) -> float:
        """
        Compute equalized odds: TPR and FPR should be similar across groups
        """
        group_tpr_fpr = {}
        
        for group, data in group_data.items():
            predictions = np.array(data['predictions'])
            actual = np.array(data['actual'])
            
            if len(predictions) == 0 or len(set(actual)) < 2:
                continue
                
            # Convert to binary classifications
            pred_binary = (predictions > 0.5).astype(int)
            
            try:
                tn, fp, fn, tp = confusion_matrix(actual, pred_binary).ravel()
                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
                group_tpr_fpr[group] = {'tpr': tpr, 'fpr': fpr}
            except ValueError:
                continue
        
        if len(group_tpr_fpr) < 2:
            return 0.0
            
        # Calculate max difference in TPR and FPR
        tprs = [metrics['tpr'] for metrics in group_tpr_fpr.values()]
        fprs = [metrics['fpr'] for metrics in group_tpr_fpr.values()]
        
        tpr_diff = max(tprs) - min(tprs)
        fpr_diff = max(fprs) - min(fprs)
        
        return max(tpr_diff, fpr_diff)
    
    def compute_calibration_parity(self, group_data: Dict[str, Dict[str, List]]) -> float:
        """
        Compute calibration parity: P(Y = 1 | Y_hat = p) should be similar across groups
        """
        group_calibrations = {}
        
        for group, data in group_data.items():
            predictions = np.array(data['predictions'])
            actual = np.array(data['actual'])
            
            if len(predictions) < 20:  # Need minimum data for calibration
                continue
            
            # Bin predictions and compute calibration
            bins = np.linspace(0, 1, 11)  # 10 bins
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            calibration_error = 0
            total_samples = 0
            
            for i in range(len(bins) - 1):
                in_bin = (predictions >= bins[i]) & (predictions < bins[i + 1])
                if np.sum(in_bin) > 0:
                    bin_accuracy = np.mean(actual[in_bin])
                    bin_confidence = np.mean(predictions[in_bin])
                    bin_size = np.sum(in_bin)
                    
                    calibration_error += bin_size * abs(bin_accuracy - bin_confidence)
                    total_samples += bin_size
            
            if total_samples > 0:
                group_calibrations[group] = calibration_error / total_samples
        
        if len(group_calibrations) < 2:
            return 0.0
            
        calibrations = list(group_calibrations.values())
        return max(calibrations) - min(calibrations)
    
    def compute_reading_ability_parity(self) -> Tuple[float, Dict[str, float]]:
        """
        Compute parity across reading ability levels (Blueprint requirement)
        """
        if not self.prediction_history:
            return 0.0, {}
            
        # Group by reading ability quartiles
        reading_abilities = [
            record['demographics'].reading_ability_level 
            for record in self.prediction_history
        ]
        
        quartiles = np.percentile(reading_abilities, [25, 50, 75])
        
        ability_groups = {
            'low': [],
            'medium_low': [],
            'medium_high': [], 
            'high': []
        }
        
        for record in self.prediction_history:
            ability = record['demographics'].reading_ability_level
            if ability <= quartiles[0]:
                group = 'low'
            elif ability <= quartiles[1]:
                group = 'medium_low'
            elif ability <= quartiles[2]:
                group = 'medium_high'
            else:
                group = 'high'
                
            ability_groups[group].append(record['predicted_mastery'])
        
        # Compute average mastery predictions per group
        group_averages = {}
        for group, predictions in ability_groups.items():
            if predictions:
                group_averages[group] = np.mean(predictions)
        
        if len(group_averages) < 2:
            return 0.0, group_averages
            
        averages = list(group_averages.values())
        parity_violation = max(averages) - min(averages)
        
        return parity_violation, group_averages
    
    def compute_language_proficiency_parity(self) -> Tuple[float, Dict[str, float]]:
        """
        Compute parity across language proficiency levels
        """
        if not self.prediction_history:
            return 0.0, {}
            
        # Group by language proficiency
        proficiency_groups = {
            'low': [],      # 0.0 - 0.33
            'medium': [],   # 0.34 - 0.66  
            'high': []      # 0.67 - 1.0
        }
        
        for record in self.prediction_history:
            proficiency = record['demographics'].language_proficiency
            if proficiency <= 0.33:
                group = 'low'
            elif proficiency <= 0.66:
                group = 'medium'
            else:
                group = 'high'
                
            proficiency_groups[group].append(record['predicted_mastery'])
        
        # Compute average mastery predictions per group
        group_averages = {}
        for group, predictions in proficiency_groups.items():
            if predictions:
                group_averages[group] = np.mean(predictions)
        
        if len(group_averages) < 2:
            return 0.0, group_averages
            
        averages = list(group_averages.values())
        parity_violation = max(averages) - min(averages)
        
        return parity_violation, group_averages
    
    def _perform_real_time_bias_check(self):
        """Perform real-time bias detection and alert generation"""
        if len(self.prediction_history) < 50:
            return  # Need minimum data
            
        # Get recent predictions (last 500)
        recent_data = self.prediction_history[-500:]
        
        # Organize data by demographic groups
        gender_groups = self._organize_by_demographic(recent_data, 'gender')
        ethnicity_groups = self._organize_by_demographic(recent_data, 'ethnicity') 
        ses_groups = self._organize_by_demographic(recent_data, 'socioeconomic_status')
        
        # Compute metrics
        metrics = FairnessMetrics(
            demographic_parity=self._compute_worst_parity(gender_groups)[0],
            equalized_odds=self.compute_equalized_odds(gender_groups),
            equality_of_opportunity=0.0,  # Placeholder
            calibration_parity=self.compute_calibration_parity(gender_groups),
            individual_fairness_score=0.0,  # Placeholder
            counterfactual_fairness=0.0,   # Placeholder  
            reading_ability_parity=self.compute_reading_ability_parity()[0],
            language_proficiency_parity=self.compute_language_proficiency_parity()[0]
        )
        
        # Check for violations and generate alerts
        self._check_violations_and_alert(metrics)
    
    def _organize_by_demographic(self, data: List[Dict], demographic_field: str) -> Dict[str, Dict[str, List]]:
        """Organize prediction data by demographic groups"""
        groups = {}
        
        for record in data:
            demo_value = getattr(record['demographics'], demographic_field)
            
            if demo_value not in groups:
                groups[demo_value] = {
                    'predictions': [],
                    'actual': []
                }
            
            groups[demo_value]['predictions'].append(record['predicted_mastery'])
            groups[demo_value]['actual'].append(record['actual_outcome'])
        
        return groups
    
    def _compute_worst_parity(self, group_data: Dict[str, Dict[str, List]]) -> Tuple[float, Dict[str, float]]:
        """Compute worst-case demographic parity violation"""
        group_predictions = {
            group: data['predictions'] 
            for group, data in group_data.items()
        }
        return self.compute_demographic_parity(group_predictions)
    
    def _check_violations_and_alert(self, metrics: FairnessMetrics):
        """Check for fairness violations and generate appropriate alerts"""
        violations = []
        
        # Check each metric against thresholds
        if metrics.demographic_parity > self.alert_thresholds['demographic_parity']:
            violations.append(('demographic_parity', metrics.demographic_parity))
            
        if metrics.equalized_odds > self.alert_thresholds['equalized_odds']:
            violations.append(('equalized_odds', metrics.equalized_odds))
            
        if metrics.calibration_parity > self.alert_thresholds['calibration_parity']:
            violations.append(('calibration_parity', metrics.calibration_parity))
            
        if metrics.reading_ability_parity > self.alert_thresholds['reading_ability_parity']:
            violations.append(('reading_ability_parity', metrics.reading_ability_parity))
            
        if metrics.language_proficiency_parity > self.alert_thresholds['language_proficiency_parity']:
            violations.append(('language_proficiency_parity', metrics.language_proficiency_parity))
        
        # Generate alerts for violations
        for violation_type, value in violations:
            self._generate_bias_alert(violation_type, value, metrics)
    
    def _generate_bias_alert(self, violation_type: str, value: float, metrics: FairnessMetrics):
        """Generate bias alert with remediation suggestions"""
        
        # Determine severity
        threshold = self.alert_thresholds[violation_type]
        if value > threshold * 3:
            severity = "critical"
        elif value > threshold * 2:
            severity = "high"
        elif value > threshold * 1.5:
            severity = "medium"
        else:
            severity = "low"
        
        # Generate remediation suggestions
        suggestions = self._get_remediation_suggestions(violation_type, severity)
        
        alert = BiasAlert(
            alert_id=f"{violation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            bias_type=violation_type,
            affected_groups=["multiple"],  # Would need more detailed analysis
            severity_level=severity,
            metric_values={violation_type: value},
            suggested_actions=suggestions,
            confidence_level=0.8  # Could be computed based on sample size
        )
        
        self.bias_alerts.append(alert)
        logger.warning(f"Bias alert generated: {violation_type} = {value:.3f} (threshold: {threshold:.3f})")
    
    def _get_remediation_suggestions(self, violation_type: str, severity: str) -> List[str]:
        """Get contextual remediation suggestions for specific bias types"""
        
        base_suggestions = {
            'demographic_parity': [
                "Review feature selection for demographic sensitivity",
                "Consider demographic-aware model training",
                "Audit question difficulty calibration across groups"
            ],
            'equalized_odds': [
                "Implement post-processing calibration by group",
                "Retrain model with fairness constraints",
                "Review ground truth label accuracy across groups"
            ],
            'calibration_parity': [
                "Apply group-specific temperature scaling",
                "Implement confidence interval adjustments",
                "Review prediction confidence thresholds"
            ],
            'reading_ability_parity': [
                "Adjust cognitive load estimates for reading ability",
                "Implement reading-level-aware question selection",
                "Add reading support features for lower ability students"
            ],
            'language_proficiency_parity': [
                "Provide multilingual support or simplified language",
                "Adjust time allocations for language processing",
                "Implement language-aware difficulty calibration"
            ]
        }
        
        suggestions = base_suggestions.get(violation_type, ["Review model fairness"])
        
        if severity in ["high", "critical"]:
            suggestions.extend([
                "Temporarily disable affected model components",
                "Implement immediate manual review process",
                "Consider emergency bias correction measures"
            ])
        
        return suggestions
    
    def generate_fairness_report(self) -> Dict[str, Any]:
        """Generate comprehensive fairness audit report"""
        
        if not self.prediction_history:
            return {"error": "No prediction data available for fairness analysis"}
        
        # Compute all fairness metrics
        recent_data = self.prediction_history[-1000:] if len(self.prediction_history) > 1000 else self.prediction_history
        
        gender_groups = self._organize_by_demographic(recent_data, 'gender')
        ethnicity_groups = self._organize_by_demographic(recent_data, 'ethnicity')
        
        metrics = FairnessMetrics(
            demographic_parity=self._compute_worst_parity(gender_groups)[0],
            equalized_odds=self.compute_equalized_odds(gender_groups),
            equality_of_opportunity=0.0,
            calibration_parity=self.compute_calibration_parity(gender_groups),
            individual_fairness_score=0.0,
            counterfactual_fairness=0.0,
            reading_ability_parity=self.compute_reading_ability_parity()[0],
            language_proficiency_parity=self.compute_language_proficiency_parity()[0]
        )
        
        # Group analysis
        reading_parity, reading_groups = self.compute_reading_ability_parity()
        language_parity, language_groups = self.compute_language_proficiency_parity()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'data_period': {
                'total_predictions': len(self.prediction_history),
                'analysis_window': len(recent_data),
                'unique_students': len(set(r['student_id'] for r in recent_data))
            },
            'fairness_metrics': {
                'demographic_parity': round(metrics.demographic_parity, 4),
                'equalized_odds': round(metrics.equalized_odds, 4),
                'calibration_parity': round(metrics.calibration_parity, 4),
                'reading_ability_parity': round(metrics.reading_ability_parity, 4),
                'language_proficiency_parity': round(metrics.language_proficiency_parity, 4)
            },
            'group_analysis': {
                'reading_ability_groups': reading_groups,
                'language_proficiency_groups': language_groups
            },
            'alerts_summary': {
                'total_alerts': len(self.bias_alerts),
                'critical_alerts': len([a for a in self.bias_alerts if a.severity_level == "critical"]),
                'recent_alerts': len([a for a in self.bias_alerts if 
                                   (datetime.now() - a.timestamp).days <= 7])
            },
            'recommendations': [
                "Implement continuous bias monitoring",
                "Add demographic-aware model calibration", 
                "Enhance reading ability assessment",
                "Provide language support features",
                "Regular fairness auditing and reporting"
            ]
        }
        
        return report
    
    def apply_bias_correction(self, student_id: str, predicted_mastery: float) -> float:
        """Apply real-time bias correction to predictions"""
        
        if student_id not in self.student_profiles:
            return predicted_mastery
            
        demographics = self.student_profiles[student_id]
        corrected_mastery = predicted_mastery
        
        # Apply reading ability correction
        if demographics.reading_ability_level < 0.5:
            # Boost predictions for lower reading ability students
            correction_factor = 0.05 * (0.5 - demographics.reading_ability_level)
            corrected_mastery += correction_factor
        
        # Apply language proficiency correction
        if demographics.language_proficiency < 0.6:
            # Boost predictions for lower language proficiency students
            correction_factor = 0.03 * (0.6 - demographics.language_proficiency)
            corrected_mastery += correction_factor
        
        # Ensure bounds
        corrected_mastery = np.clip(corrected_mastery, 0.0, 1.0)
        
        return corrected_mastery