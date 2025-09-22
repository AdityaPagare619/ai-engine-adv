# Time-Aware Intelligence Engine
# Phase 2-3 Strategic Implementation as per Roadmap

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)

class ExamPhase(Enum):
    """Strategic preparation phases based on time to exam"""
    FOUNDATION = "foundation"      # 6+ months
    BUILDING = "building"          # 3-6 months  
    MASTERY = "mastery"            # 1-3 months
    CONFIDENCE = "confidence"      # Final month

class StudentClass(Enum):
    """Student academic year classification"""
    CLASS_11 = "11th"
    CLASS_12 = "12th" 
    DROPPER = "dropper"

@dataclass
class ExamSchedule:
    """JEE/NEET exam schedule management"""
    exam_name: str
    january_session: Optional[datetime] = None
    april_session: Optional[datetime] = None
    main_exam_date: Optional[datetime] = None
    advanced_exam_date: Optional[datetime] = None
    
    @classmethod
    def get_2025_schedule(cls) -> Dict[str, 'ExamSchedule']:
        """Official 2025 JEE/NEET schedule"""
        return {
            "JEE_MAIN": cls(
                exam_name="JEE Main",
                january_session=datetime(2025, 1, 24),
                april_session=datetime(2025, 4, 1),
                main_exam_date=datetime(2025, 4, 1)
            ),
            "JEE_ADVANCED": cls(
                exam_name="JEE Advanced",
                main_exam_date=datetime(2025, 5, 18)
            ),
            "NEET": cls(
                exam_name="NEET",
                main_exam_date=datetime(2025, 5, 4)
            )
        }

@dataclass
class TimeAwareStrategy:
    """Strategic learning plan based on time analysis"""
    exam_dates: Dict[str, datetime]
    current_phase: ExamPhase
    days_remaining: Dict[str, int]
    preparation_timeline: Dict[str, List[str]]
    strategic_milestones: List[Tuple[datetime, str]]
    recommended_daily_hours: float
    priority_concepts: List[str]
    confidence_building_topics: List[str]

class TimeAwareExamEngine:
    """
    Time-aware exam preparation engine matching roadmap specifications
    Provides strategic test planning and phase-based optimization
    """
    
    def __init__(self):
        self.exam_schedules = ExamSchedule.get_2025_schedule()
        self.phase_strategies = self._initialize_phase_strategies()
        logger.info("Time-aware exam engine initialized with 2025 schedules")
    
    def _initialize_phase_strategies(self) -> Dict[ExamPhase, Dict[str, Any]]:
        """Initialize phase-specific learning strategies"""
        return {
            ExamPhase.FOUNDATION: {
                "focus": "concept_building",
                "difficulty_range": (0.2, 0.6),
                "daily_hours": 4.0,
                "topics_per_session": 3,
                "revision_frequency": 7,  # days
                "description": "Build strong conceptual foundation"
            },
            ExamPhase.BUILDING: {
                "focus": "skill_development", 
                "difficulty_range": (0.4, 0.8),
                "daily_hours": 5.0,
                "topics_per_session": 4,
                "revision_frequency": 5,
                "description": "Develop problem-solving skills"
            },
            ExamPhase.MASTERY: {
                "focus": "advanced_practice",
                "difficulty_range": (0.6, 0.9),
                "daily_hours": 6.0,
                "topics_per_session": 5,
                "revision_frequency": 3,
                "description": "Master advanced concepts and applications"
            },
            ExamPhase.CONFIDENCE: {
                "focus": "confidence_building",
                "difficulty_range": (0.3, 0.7),
                "daily_hours": 4.0,
                "topics_per_session": 6,
                "revision_frequency": 1,
                "description": "Build confidence with targeted practice"
            }
        }
    
    def calculate_exam_timeline(self, 
                              student_class: StudentClass, 
                              target_exams: List[str],
                              preferred_attempt_year: Optional[int] = None) -> TimeAwareStrategy:
        """
        Calculate strategic exam timeline based on student status
        Core functionality from roadmap Phase 2-3
        """
        current_date = datetime.now()
        
        # Determine target year based on student class
        if student_class == StudentClass.CLASS_11:
            target_year = current_date.year + 1
        elif student_class == StudentClass.CLASS_12:
            if current_date.month <= 6:  # Before main exam season
                target_year = current_date.year
            else:  # After main exams, prepare for next cycle
                target_year = current_date.year + 1
        elif student_class == StudentClass.DROPPER:
            target_year = preferred_attempt_year or current_date.year + 1
        else:
            target_year = current_date.year + 1
            
        # Get exam dates for target year
        exam_dates = {}
        days_remaining = {}
        
        for exam_name in target_exams:
            if exam_name in self.exam_schedules:
                schedule = self.exam_schedules[exam_name]
                # Adjust dates to target year
                if schedule.main_exam_date:
                    exam_date = schedule.main_exam_date.replace(year=target_year)
                    exam_dates[exam_name] = exam_date
                    days_remaining[exam_name] = (exam_date - current_date).days
        
        # Determine current phase based on closest exam
        min_days = min(days_remaining.values()) if days_remaining else 365
        current_phase = self._determine_phase(min_days)
        
        # Generate preparation timeline
        preparation_timeline = self._generate_preparation_timeline(
            current_phase, days_remaining, target_exams
        )
        
        # Generate strategic milestones
        strategic_milestones = self._generate_strategic_milestones(
            current_date, exam_dates, current_phase
        )
        
        # Get phase strategy
        phase_strategy = self.phase_strategies[current_phase]
        
        # Calculate priority concepts based on phase and exam type
        priority_concepts = self._calculate_priority_concepts(
            current_phase, target_exams, days_remaining
        )
        
        # Calculate confidence building topics for final phase
        confidence_building_topics = self._calculate_confidence_topics(
            current_phase, target_exams
        )
        
        return TimeAwareStrategy(
            exam_dates=exam_dates,
            current_phase=current_phase,
            days_remaining=days_remaining,
            preparation_timeline=preparation_timeline,
            strategic_milestones=strategic_milestones,
            recommended_daily_hours=phase_strategy["daily_hours"],
            priority_concepts=priority_concepts,
            confidence_building_topics=confidence_building_topics
        )
    
    def _determine_phase(self, days_remaining: int) -> ExamPhase:
        """Determine current preparation phase based on days to exam"""
        if days_remaining > 180:  # 6+ months
            return ExamPhase.FOUNDATION
        elif days_remaining > 90:  # 3-6 months
            return ExamPhase.BUILDING
        elif days_remaining > 30:  # 1-3 months
            return ExamPhase.MASTERY
        else:  # Final month
            return ExamPhase.CONFIDENCE
    
    def _generate_preparation_timeline(self, 
                                     current_phase: ExamPhase,
                                     days_remaining: Dict[str, int],
                                     target_exams: List[str]) -> Dict[str, List[str]]:
        """Generate detailed preparation timeline"""
        timeline = {}
        
        for exam_name, days in days_remaining.items():
            if exam_name == "JEE_MAIN":
                timeline[exam_name] = self._generate_jee_main_timeline(current_phase, days)
            elif exam_name == "JEE_ADVANCED":
                timeline[exam_name] = self._generate_jee_advanced_timeline(current_phase, days)
            elif exam_name == "NEET":
                timeline[exam_name] = self._generate_neet_timeline(current_phase, days)
        
        return timeline
    
    def _generate_jee_main_timeline(self, phase: ExamPhase, days: int) -> List[str]:
        """Generate JEE Main specific timeline"""
        if phase == ExamPhase.FOUNDATION:
            return [
                "Complete NCERT Mathematics (Classes 11-12)",
                "Master basic Physics concepts",
                "Build Chemistry foundation",
                "Start solving basic numerical problems",
                "Regular mock tests (weekly)"
            ]
        elif phase == ExamPhase.BUILDING:
            return [
                "Advanced problem solving in all subjects",
                "Previous year questions practice",
                "Chapter-wise tests",
                "Time management drills",
                "Identify and work on weak areas"
            ]
        elif phase == ExamPhase.MASTERY:
            return [
                "Full-length mock tests (daily)",
                "Advanced level questions",
                "Speed and accuracy improvement",
                "Revision of all important formulas",
                "Strategy optimization"
            ]
        else:  # CONFIDENCE
            return [
                "Focus on high-scoring topics",
                "Quick revision of strong concepts",
                "Light practice to maintain momentum",
                "Stress management techniques",
                "Final strategy review"
            ]
    
    def _generate_jee_advanced_timeline(self, phase: ExamPhase, days: int) -> List[str]:
        """Generate JEE Advanced specific timeline"""
        if phase == ExamPhase.FOUNDATION:
            return [
                "Deep conceptual understanding",
                "Advanced Mathematics topics",
                "Complex Physics problems",
                "Organic Chemistry mechanisms",
                "Build analytical thinking"
            ]
        elif phase == ExamPhase.BUILDING:
            return [
                "Multi-concept integrated problems",
                "JEE Advanced previous years",
                "Complex numerical problems",
                "Time-bound practice",
                "Advanced problem-solving techniques"
            ]
        elif phase == ExamPhase.MASTERY:
            return [
                "Full JEE Advanced pattern tests",
                "Multi-part question practice",
                "Negative marking strategy",
                "Advanced concept application",
                "Peak performance optimization"
            ]
        else:  # CONFIDENCE
            return [
                "Confidence building with known topics",
                "Quick formula revision",
                "Strategy finalization",
                "Mental preparation",
                "Maintain problem-solving sharpness"
            ]
    
    def _generate_neet_timeline(self, phase: ExamPhase, days: int) -> List[str]:
        """Generate NEET specific timeline"""
        if phase == ExamPhase.FOUNDATION:
            return [
                "Complete NCERT Biology thoroughly",
                "Build strong Chemistry concepts",
                "Master Physics fundamentals",
                "Develop factual recall ability",
                "Regular biology diagram practice"
            ]
        elif phase == ExamPhase.BUILDING:
            return [
                "Advanced Biology topics",
                "Chemical reactions and mechanisms",
                "Physics numerical problems",
                "Previous year question analysis",
                "Speed reading and retention"
            ]
        elif phase == ExamPhase.MASTERY:
            return [
                "NEET pattern mock tests",
                "Factual questions rapid fire",
                "Time management for 180 questions",
                "Biology classification mastery",
                "Final concept consolidation"
            ]
        else:  # CONFIDENCE
            return [
                "High-yield topics revision",
                "Important facts quick review",
                "Biology diagrams practice",
                "Confidence building exercises",
                "Exam day strategy"
            ]
    
    def _generate_strategic_milestones(self, 
                                     current_date: datetime,
                                     exam_dates: Dict[str, datetime],
                                     current_phase: ExamPhase) -> List[Tuple[datetime, str]]:
        """Generate strategic milestone calendar"""
        milestones = []
        
        for exam_name, exam_date in exam_dates.items():
            # Calculate milestone dates
            if current_phase == ExamPhase.FOUNDATION:
                milestones.extend([
                    (current_date + timedelta(days=30), f"Complete {exam_name} syllabus review"),
                    (current_date + timedelta(days=60), f"Begin {exam_name} advanced topics"),
                    (current_date + timedelta(days=90), f"Start {exam_name} previous year practice")
                ])
            elif current_phase == ExamPhase.BUILDING:
                milestones.extend([
                    (current_date + timedelta(days=15), f"{exam_name} weak area improvement"),
                    (current_date + timedelta(days=30), f"{exam_name} mock test series begin"),
                    (current_date + timedelta(days=45), f"{exam_name} strategy optimization")
                ])
            elif current_phase == ExamPhase.MASTERY:
                milestones.extend([
                    (current_date + timedelta(days=7), f"{exam_name} daily mocks begin"),
                    (current_date + timedelta(days=14), f"{exam_name} performance analysis"),
                    (current_date + timedelta(days=21), f"{exam_name} final revision phase")
                ])
            else:  # CONFIDENCE
                milestones.extend([
                    (exam_date - timedelta(days=7), f"{exam_name} final preparation"),
                    (exam_date - timedelta(days=3), f"{exam_name} confidence building"),
                    (exam_date - timedelta(days=1), f"{exam_name} final review")
                ])
        
        # Sort milestones by date
        milestones.sort(key=lambda x: x[0])
        return milestones
    
    def _calculate_priority_concepts(self, 
                                   phase: ExamPhase,
                                   target_exams: List[str],
                                   days_remaining: Dict[str, int]) -> List[str]:
        """Calculate priority concepts based on phase and exam proximity"""
        priority_concepts = []
        
        # Base concepts by exam type
        exam_concepts = {
            "JEE_MAIN": [
                "calculus", "algebra", "coordinate_geometry", "mechanics", 
                "thermodynamics", "electromagnetism", "organic_chemistry",
                "inorganic_chemistry", "physical_chemistry"
            ],
            "JEE_ADVANCED": [
                "advanced_calculus", "complex_numbers", "advanced_mechanics",
                "quantum_physics", "advanced_organic", "coordination_chemistry",
                "advanced_algebra", "differential_equations"
            ],
            "NEET": [
                "human_physiology", "plant_physiology", "genetics", "ecology",
                "organic_chemistry", "inorganic_chemistry", "mechanics",
                "thermodynamics", "optics"
            ]
        }
        
        for exam in target_exams:
            if exam in exam_concepts:
                concepts = exam_concepts[exam]
                
                # Adjust priority based on phase
                if phase == ExamPhase.CONFIDENCE:
                    # Focus on high-scoring, well-mastered topics
                    priority_concepts.extend(concepts[:5])
                else:
                    priority_concepts.extend(concepts)
        
        return list(set(priority_concepts))  # Remove duplicates
    
    def _calculate_confidence_topics(self, 
                                   phase: ExamPhase,
                                   target_exams: List[str]) -> List[str]:
        """Calculate confidence building topics for final phase"""
        if phase != ExamPhase.CONFIDENCE:
            return []
        
        confidence_topics = []
        
        for exam in target_exams:
            if exam == "JEE_MAIN":
                confidence_topics.extend([
                    "basic_algebra", "coordinate_geometry_basics", "simple_mechanics",
                    "basic_organic_reactions", "periodic_table"
                ])
            elif exam == "NEET":
                confidence_topics.extend([
                    "human_anatomy_basics", "plant_structure", "basic_genetics",
                    "simple_organic_compounds", "basic_physics_formulas"
                ])
        
        return confidence_topics
    
    def generate_daily_study_plan(self, 
                                strategy: TimeAwareStrategy,
                                student_masteries: Dict[str, float],
                                target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate optimized daily study plan based on strategy"""
        target_date = target_date or datetime.now()
        
        # Get phase strategy
        phase_strategy = self.phase_strategies[strategy.current_phase]
        
        # Calculate study distribution
        total_hours = phase_strategy["daily_hours"]
        topics_count = phase_strategy["topics_per_session"]
        
        # Prioritize based on masteries and phase
        study_topics = []
        for concept in strategy.priority_concepts[:topics_count]:
            mastery = student_masteries.get(concept, 0.3)
            
            # Calculate time allocation based on mastery and phase
            if strategy.current_phase == ExamPhase.CONFIDENCE:
                # More time on strong topics for confidence
                time_weight = 1.2 if mastery > 0.7 else 0.8
            else:
                # More time on weak topics for improvement
                time_weight = 1.5 - mastery  # More time for lower mastery
            
            study_topics.append({
                "concept": concept,
                "mastery": mastery,
                "allocated_time": (total_hours / topics_count) * time_weight,
                "difficulty_range": phase_strategy["difficulty_range"],
                "focus": phase_strategy["focus"]
            })
        
        return {
            "date": target_date.isoformat(),
            "phase": strategy.current_phase.value,
            "total_study_hours": total_hours,
            "study_topics": study_topics,
            "revision_topics": self._calculate_revision_topics(
                strategy, student_masteries, target_date
            ),
            "break_intervals": self._calculate_optimal_breaks(total_hours),
            "motivation_message": self._generate_motivation_message(strategy)
        }
    
    def _calculate_revision_topics(self, 
                                 strategy: TimeAwareStrategy,
                                 masteries: Dict[str, float],
                                 date: datetime) -> List[str]:
        """Calculate topics needing revision based on time decay"""
        revision_topics = []
        revision_freq = self.phase_strategies[strategy.current_phase]["revision_frequency"]
        
        # Simple heuristic: concepts with good mastery but no recent practice
        for concept, mastery in masteries.items():
            if mastery > 0.6 and date.day % revision_freq == 0:
                revision_topics.append(concept)
        
        return revision_topics[:3]  # Limit to 3 revision topics per day
    
    def _calculate_optimal_breaks(self, total_hours: float) -> List[Tuple[float, int]]:
        """Calculate optimal break intervals using Pomodoro-like technique"""
        breaks = []
        study_blocks = math.ceil(total_hours * 2)  # 30-minute blocks
        
        for i in range(study_blocks):
            if i > 0 and i % 4 == 0:  # Long break after 4 blocks (2 hours)
                breaks.append((i * 0.5, 15))  # 15-minute break
            elif i > 0 and i % 2 == 0:  # Short break after 2 blocks (1 hour)
                breaks.append((i * 0.5, 5))   # 5-minute break
        
        return breaks
    
    def _generate_motivation_message(self, strategy: TimeAwareStrategy) -> str:
        """Generate phase-appropriate motivation message"""
        messages = {
            ExamPhase.FOUNDATION: "Building strong foundations leads to unshakeable success! 🏗️",
            ExamPhase.BUILDING: "Every problem solved is a step closer to your dream! 💪", 
            ExamPhase.MASTERY: "You're in the zone! Master every concept with confidence! 🎯",
            ExamPhase.CONFIDENCE: "Trust your preparation. You've got this! 🌟"
        }
        
        days_msg = ""
        if strategy.days_remaining:
            min_days = min(strategy.days_remaining.values())
            days_msg = f" Only {min_days} days to go!"
        
        return messages[strategy.current_phase] + days_msg

# Integration with main BKT engine
class TimeAwareBKTIntegration:
    """Integration layer between time-aware engine and main BKT system"""
    
    def __init__(self, time_engine: TimeAwareExamEngine):
        self.time_engine = time_engine
        
    def get_context_adjustments(self, 
                               student_id: str,
                               concept_id: str, 
                               strategy: TimeAwareStrategy) -> Dict[str, float]:
        """Get BKT parameter adjustments based on time-aware strategy"""
        
        phase_adjustments = {
            ExamPhase.FOUNDATION: {
                "learn_rate_boost": 0.1,      # More learning in foundation
                "difficulty_preference": 0.4,  # Moderate difficulty
                "confidence_weight": 0.8       # Lower confidence requirement
            },
            ExamPhase.BUILDING: {
                "learn_rate_boost": 0.05,     # Standard learning
                "difficulty_preference": 0.6,  # Higher difficulty  
                "confidence_weight": 0.9       # Higher confidence requirement
            },
            ExamPhase.MASTERY: {
                "learn_rate_boost": 0.0,      # No boost, rely on mastery
                "difficulty_preference": 0.8,  # High difficulty
                "confidence_weight": 0.95      # Very high confidence requirement
            },
            ExamPhase.CONFIDENCE: {
                "learn_rate_boost": -0.05,    # Slight reduction for stability
                "difficulty_preference": 0.5,  # Moderate for confidence
                "confidence_weight": 0.7       # Lower requirement for confidence
            }
        }
        
        adjustments = phase_adjustments[strategy.current_phase]
        
        # Additional adjustments based on concept priority
        if concept_id in strategy.priority_concepts:
            adjustments["learn_rate_boost"] += 0.05
            
        if concept_id in strategy.confidence_building_topics:
            adjustments["difficulty_preference"] -= 0.1
            adjustments["confidence_weight"] -= 0.1
            
        return adjustments