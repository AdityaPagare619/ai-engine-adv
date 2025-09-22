# Time Context Processor - Exam Countdown Intelligence
# Integrates with your BKT engine for time-aware recommendations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class ExamPhase(Enum):
    FOUNDATION = "foundation"      # > 90 days
    BUILDING = "building"          # 60-90 days  
    MASTERY = "mastery"           # 30-60 days
    CONFIDENCE = "confidence"      # 0-30 days

@dataclass
class TimeContext:
    exam_date: datetime
    days_remaining: int
    phase: ExamPhase
    urgency_level: str
    recommended_focus: List[str]
    daily_study_hours: float
    weekly_targets: Dict[str, int]

class TimeContextProcessor:
    """
    Time-aware exam preparation intelligence
    Provides phase-based recommendations integrated with BKT mastery data
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Phase-based study parameters
        self.phase_configs = {
            ExamPhase.FOUNDATION: {
                'daily_hours': 6.0,
                'concept_coverage': 0.7,  # Cover 70% of syllabus
                'mastery_threshold': 0.4,  # Basic understanding
                'focus_areas': ['concept_building', 'foundation_strengthening'],
                'practice_ratio': 0.3      # 30% practice, 70% learning
            },
            ExamPhase.BUILDING: {
                'daily_hours': 7.0,
                'concept_coverage': 0.9,   # Cover 90% of syllabus
                'mastery_threshold': 0.6,  # Good understanding
                'focus_areas': ['skill_development', 'problem_solving'],
                'practice_ratio': 0.5      # 50% practice, 50% learning
            },
            ExamPhase.MASTERY: {
                'daily_hours': 8.0,
                'concept_coverage': 1.0,   # Complete syllabus
                'mastery_threshold': 0.8,  # Strong mastery
                'focus_areas': ['advanced_problems', 'speed_building'],
                'practice_ratio': 0.7      # 70% practice, 30% learning
            },
            ExamPhase.CONFIDENCE: {
                'daily_hours': 8.0,
                'concept_coverage': 1.0,   # Maintain coverage
                'mastery_threshold': 0.9,  # Near mastery
                'focus_areas': ['revision', 'mock_tests', 'confidence_building'],
                'practice_ratio': 0.9      # 90% practice, 10% new learning
            }
        }
    
    def get_time_context(self, exam_date: datetime, current_date: Optional[datetime] = None) -> TimeContext:
        """Get current time context for exam preparation"""
        if current_date is None:
            current_date = datetime.now()
        
        # Calculate days remaining
        time_diff = exam_date - current_date
        days_remaining = max(0, time_diff.days)
        
        # Determine phase
        phase = self._determine_phase(days_remaining)
        
        # Get phase configuration
        config = self.phase_configs[phase]
        
        # Determine urgency level
        urgency_level = self._calculate_urgency(days_remaining, phase)
        
        # Generate recommendations
        recommended_focus = self._generate_focus_recommendations(phase, days_remaining)
        
        # Calculate weekly targets
        weekly_targets = self._calculate_weekly_targets(phase, days_remaining)
        
        return TimeContext(
            exam_date=exam_date,
            days_remaining=days_remaining,
            phase=phase,
            urgency_level=urgency_level,
            recommended_focus=recommended_focus,
            daily_study_hours=config['daily_hours'],
            weekly_targets=weekly_targets
        )
    
    def _determine_phase(self, days_remaining: int) -> ExamPhase:
        """Determine current preparation phase based on days remaining"""
        if days_remaining > 90:
            return ExamPhase.FOUNDATION
        elif days_remaining > 60:
            return ExamPhase.BUILDING
        elif days_remaining > 30:
            return ExamPhase.MASTERY
        else:
            return ExamPhase.CONFIDENCE
    
    def _calculate_urgency(self, days_remaining: int, phase: ExamPhase) -> str:
        """Calculate urgency level"""
        if days_remaining < 7:
            return "critical"
        elif days_remaining < 30:
            return "high" 
        elif days_remaining < 90:
            return "medium"
        else:
            return "low"
    
    def _generate_focus_recommendations(self, phase: ExamPhase, days_remaining: int) -> List[str]:
        """Generate phase-specific focus recommendations"""
        config = self.phase_configs[phase]
        base_focus = config['focus_areas'].copy()
        
        # Add time-specific recommendations
        if phase == ExamPhase.CONFIDENCE:
            if days_remaining < 7:
                base_focus.extend(['light_revision', 'stress_management', 'exam_strategy'])
            elif days_remaining < 15:
                base_focus.extend(['full_mock_tests', 'time_management'])
        
        elif phase == ExamPhase.MASTERY:
            if days_remaining < 40:
                base_focus.extend(['weak_area_focus', 'speed_enhancement'])
        
        elif phase == ExamPhase.BUILDING:
            if days_remaining < 75:
                base_focus.extend(['concept_integration', 'problem_patterns'])
        
        return base_focus
    
    def _calculate_weekly_targets(self, phase: ExamPhase, days_remaining: int) -> Dict[str, int]:
        """Calculate weekly study targets based on phase"""
        config = self.phase_configs[phase]
        
        # Base targets
        targets = {
            'new_concepts': 0,
            'practice_problems': 0,
            'revision_hours': 0,
            'mock_tests': 0
        }
        
        if phase == ExamPhase.FOUNDATION:
            targets.update({
                'new_concepts': 15,
                'practice_problems': 50,
                'revision_hours': 10,
                'mock_tests': 1
            })
        
        elif phase == ExamPhase.BUILDING:
            targets.update({
                'new_concepts': 10,
                'practice_problems': 80,
                'revision_hours': 15,
                'mock_tests': 2
            })
        
        elif phase == ExamPhase.MASTERY:
            targets.update({
                'new_concepts': 5,
                'practice_problems': 120,
                'revision_hours': 20,
                'mock_tests': 3
            })
        
        elif phase == ExamPhase.CONFIDENCE:
            targets.update({
                'new_concepts': 0,
                'practice_problems': 150,
                'revision_hours': 25,
                'mock_tests': 4
            })
        
        return targets
    
    def get_strategic_recommendations(self, 
                                   time_context: TimeContext,
                                   student_mastery_profile: Dict) -> Dict:
        """
        Generate strategic recommendations based on time context and mastery
        Integrates with BKT engine data
        """
        try:
            phase_config = self.phase_configs[time_context.phase]
            
            # Analyze mastery gaps
            weak_concepts = []
            strong_concepts = []
            
            if 'concept_details' in student_mastery_profile:
                for concept_id, details in student_mastery_profile['concept_details'].items():
                    mastery = details.get('mastery', 0)
                    if mastery < phase_config['mastery_threshold']:
                        weak_concepts.append({
                            'concept': concept_id,
                            'mastery': mastery,
                            'priority': 'high' if mastery < 0.3 else 'medium'
                        })
                    elif mastery > 0.8:
                        strong_concepts.append(concept_id)
            
            # Generate time-aware recommendations
            recommendations = {
                'immediate_actions': self._get_immediate_actions(time_context, weak_concepts),
                'study_plan': self._generate_study_plan(time_context, weak_concepts, strong_concepts),
                'priority_concepts': [c['concept'] for c in weak_concepts[:5]],  # Top 5 priorities
                'daily_schedule': self._create_daily_schedule(time_context, phase_config),
                'milestone_targets': self._create_milestones(time_context),
                'risk_assessment': self._assess_preparation_risk(time_context, student_mastery_profile)
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating strategic recommendations: {e}")
            return {'error': str(e)}
    
    def _get_immediate_actions(self, time_context: TimeContext, weak_concepts: List[Dict]) -> List[str]:
        """Get immediate actionable recommendations"""
        actions = []
        
        if time_context.urgency_level == "critical":
            actions.extend([
                "Focus only on high-yield topics",
                "Complete quick revision of formulas",
                "Practice previous year questions",
                "Take final mock test"
            ])
        elif time_context.urgency_level == "high":
            actions.extend([
                "Prioritize weak areas identified",
                "Increase daily practice problems",
                "Schedule mock tests every 3 days",
                "Create formula sheets for quick revision"
            ])
        elif weak_concepts:
            top_weak = weak_concepts[:3]
            for concept in top_weak:
                actions.append(f"Focus on {concept['concept']} (current mastery: {concept['mastery']:.2f})")
        
        return actions
    
    def _generate_study_plan(self, time_context: TimeContext, 
                           weak_concepts: List[Dict], strong_concepts: List[str]) -> Dict:
        """Generate detailed study plan"""
        phase_config = self.phase_configs[time_context.phase]
        
        plan = {
            'daily_hours': phase_config['daily_hours'],
            'practice_ratio': phase_config['practice_ratio'],
            'learning_ratio': 1 - phase_config['practice_ratio'],
            'time_allocation': {}
        }
        
        total_hours = phase_config['daily_hours']
        practice_hours = total_hours * phase_config['practice_ratio']
        learning_hours = total_hours * (1 - phase_config['practice_ratio'])
        
        plan['time_allocation'] = {
            'new_learning': learning_hours,
            'practice_problems': practice_hours * 0.7,
            'revision': practice_hours * 0.2,
            'mock_tests': practice_hours * 0.1
        }
        
        return plan
    
    def _create_daily_schedule(self, time_context: TimeContext, phase_config: Dict) -> Dict:
        """Create suggested daily schedule"""
        return {
            'morning_session': {
                'duration': '3 hours',
                'focus': 'new_concepts' if time_context.phase in [ExamPhase.FOUNDATION, ExamPhase.BUILDING] else 'practice',
                'energy_level': 'high'
            },
            'afternoon_session': {
                'duration': '2.5 hours', 
                'focus': 'practice_problems',
                'energy_level': 'medium'
            },
            'evening_session': {
                'duration': '2.5 hours',
                'focus': 'revision_and_weak_areas',
                'energy_level': 'medium'
            },
            'breaks': {
                'short_breaks': '15 min every 90 min',
                'lunch_break': '1 hour',
                'recreation': '1 hour'
            }
        }
    
    def _create_milestones(self, time_context: TimeContext) -> List[Dict]:
        """Create time-based milestones"""
        milestones = []
        days_remaining = time_context.days_remaining
        
        # Create milestones based on remaining time
        if days_remaining > 60:
            milestones.extend([
                {'target_date': days_remaining - 45, 'goal': 'Complete 70% syllabus coverage'},
                {'target_date': days_remaining - 30, 'goal': 'Achieve 60% average mastery'},
                {'target_date': days_remaining - 15, 'goal': 'Complete first comprehensive mock'}
            ])
        elif days_remaining > 30:
            milestones.extend([
                {'target_date': days_remaining - 20, 'goal': 'Strengthen all weak areas'},
                {'target_date': days_remaining - 10, 'goal': 'Achieve 80% average mastery'},
                {'target_date': days_remaining - 5, 'goal': 'Complete final preparation'}
            ])
        else:
            milestones.extend([
                {'target_date': max(1, days_remaining - 10), 'goal': 'Complete all practice tests'},
                {'target_date': max(1, days_remaining - 5), 'goal': 'Final weak area revision'},
                {'target_date': 1, 'goal': 'Light revision and exam preparation'}
            ])
        
        return milestones
    
    def _assess_preparation_risk(self, time_context: TimeContext, mastery_profile: Dict) -> Dict:
        """Assess risk level of current preparation"""
        overall_mastery = mastery_profile.get('overall_mastery', 0)
        phase_config = self.phase_configs[time_context.phase]
        required_mastery = phase_config['mastery_threshold']
        
        mastery_gap = required_mastery - overall_mastery
        
        if mastery_gap > 0.3:
            risk_level = "high"
            risk_message = f"Significant preparation gap. Need {mastery_gap:.2f} improvement in mastery."
        elif mastery_gap > 0.1:
            risk_level = "medium" 
            risk_message = f"Moderate preparation gap. Need {mastery_gap:.2f} improvement in mastery."
        else:
            risk_level = "low"
            risk_message = "On track with preparation goals."
        
        return {
            'risk_level': risk_level,
            'message': risk_message,
            'mastery_gap': round(mastery_gap, 3),
            'required_mastery': required_mastery,
            'current_mastery': round(overall_mastery, 3)
        }
    
    def integrate_with_bkt(self, bkt_engine, student_id: str, exam_date: datetime) -> Dict:
        """
        Integration method with your BKT engine
        """
        try:
            # Get time context
            time_context = self.get_time_context(exam_date)
            
            # Get student profile from BKT
            student_profile = bkt_engine.get_student_profile(student_id)
            
            if 'error' in student_profile:
                return student_profile
            
            # Generate strategic recommendations
            recommendations = self.get_strategic_recommendations(time_context, student_profile)
            
            return {
                'student_id': student_id,
                'time_context': {
                    'days_remaining': time_context.days_remaining,
                    'phase': time_context.phase.value,
                    'urgency_level': time_context.urgency_level,
                    'daily_study_hours': time_context.daily_study_hours
                },
                'mastery_summary': {
                    'overall_mastery': student_profile.get('overall_mastery', 0),
                    'strong_concepts': student_profile.get('strong_concepts', []),
                    'weak_concepts': student_profile.get('weak_concepts', [])
                },
                'recommendations': recommendations,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error integrating with BKT: {e}")
            return {'success': False, 'error': str(e)}