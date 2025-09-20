#!/usr/bin/env python3
"""
Advanced 3-Month Human-Like Student Simulation Framework
Realistic behavioral modeling for comprehensive Phase 4B testing
"""

import asyncio
import random
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy.stats import lognorm, beta, gamma
import math

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('human_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"

class PersonalityType(Enum):
    CONSCIENTIOUS = "conscientious"
    PROCRASTINATOR = "procrastinator" 
    PERFECTIONIST = "perfectionist"
    ANXIETY_PRONE = "anxiety_prone"
    CONFIDENT = "confident"

class MotivationState(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BURNOUT = "burnout"

@dataclass
class PsychologicalProfile:
    """Comprehensive psychological profile for realistic behavior simulation"""
    
    # Big Five Personality Traits (0.0-1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    # Cognitive Characteristics
    working_memory_capacity: float = 7.0  # Miller's 7±2
    processing_speed: float = 1.0  # Relative to baseline
    attention_span_minutes: float = 45.0
    
    # Learning Characteristics  
    learning_style: LearningStyle = LearningStyle.VISUAL
    preferred_difficulty_growth: float = 0.1  # Per session
    stress_tolerance: float = 0.6
    perfectionism_level: float = 0.3
    
    # Individual Differences
    reading_speed_wpm: float = 250.0
    math_anxiety_level: float = 0.2
    impulsiveness: float = 0.3
    help_seeking_tendency: float = 0.4

@dataclass
class DailyState:
    """Dynamic daily state variables"""
    date: datetime
    mood: float = 0.5  # 0.0 (terrible) to 1.0 (excellent)
    energy_level: float = 0.8
    motivation: float = 0.6
    stress_baseline: float = 0.2
    sleep_quality: float = 0.7  # Previous night's sleep
    life_events_impact: float = 0.0  # External stressors
    
    # Session-specific states
    current_fatigue: float = 0.0
    accumulated_stress: float = 0.0
    session_motivation: float = 0.6

@dataclass 
class LearningSession:
    """Individual learning session data"""
    session_id: str
    date: datetime
    start_time: datetime
    duration_minutes: float
    questions_attempted: int
    questions_correct: int
    topics_covered: List[str]
    avg_response_time_ms: float
    peak_stress_level: float
    final_fatigue_level: float
    break_requests: int
    help_requests: int
    mastery_gains: Dict[str, float]
    engagement_score: float

class AdvancedHumanSimulator:
    """
    Sophisticated human-like behavior simulator for educational AI testing
    
    Simulates realistic learning patterns including:
    - Personality-driven behavior variations
    - Daily mood and energy fluctuations
    - Realistic knowledge decay and retention
    - Authentic stress and fatigue accumulation
    - Individual learning style preferences
    - Motivation cycles and academic burnout
    """
    
    def __init__(self, student_profile: PsychologicalProfile, student_id: str):
        self.profile = student_profile
        self.student_id = student_id
        self.learning_history: List[LearningSession] = []
        self.knowledge_state: Dict[str, float] = {}  # Topic -> mastery level
        self.motivation_trend = []
        self.stress_trend = []
        
        # Initialize baseline knowledge for different topics
        self.topics = [
            "algebra_basics", "geometry_fundamentals", "calculus_intro", 
            "statistics_basic", "trigonometry", "linear_equations",
            "quadratic_equations", "probability", "functions", "derivatives"
        ]
        
        # Initialize knowledge based on profile
        for topic in self.topics:
            # Some natural variation in starting knowledge
            base_knowledge = random.uniform(0.1, 0.4)
            self.knowledge_state[topic] = base_knowledge
            
    def generate_daily_state(self, day: int, base_profile: PsychologicalProfile) -> DailyState:
        """Generate realistic daily psychological and physiological state"""
        
        # Weekly patterns (lower energy on Mondays, higher on Fridays)
        week_day = day % 7
        weekly_energy_modifier = {0: -0.1, 1: -0.05, 2: 0.0, 3: 0.05, 4: 0.1, 5: 0.05, 6: -0.1}
        
        # Monthly motivation cycles (natural ups and downs)
        motivation_cycle = 0.1 * math.sin(2 * math.pi * day / 30)
        
        # Seasonal effects (assuming start in September)
        seasonal_effect = 0.05 * math.sin(2 * math.pi * day / 365)
        
        # Random daily variations
        daily_mood_variation = np.random.normal(0, 0.1)
        daily_energy_variation = np.random.normal(0, 0.1)
        
        # Personality-based baseline adjustments
        personality_mood_boost = (
            base_profile.extraversion * 0.1 + 
            (1 - base_profile.neuroticism) * 0.1 +
            base_profile.conscientiousness * 0.05
        )
        
        # Generate external life events occasionally
        life_event_probability = 0.05  # 5% chance per day
        life_events_impact = 0.0
        if random.random() < life_event_probability:
            # Random life event (positive or negative)
            life_events_impact = random.uniform(-0.3, 0.2)
            
        return DailyState(
            date=datetime.now() + timedelta(days=day),
            mood=np.clip(0.6 + personality_mood_boost + daily_mood_variation + seasonal_effect + life_events_impact, 0.0, 1.0),
            energy_level=np.clip(0.75 + weekly_energy_modifier[week_day] + daily_energy_variation, 0.2, 1.0),
            motivation=np.clip(0.6 + motivation_cycle + base_profile.conscientiousness * 0.2, 0.1, 1.0),
            stress_baseline=np.clip(base_profile.neuroticism * 0.3 + abs(life_events_impact), 0.0, 0.8),
            sleep_quality=np.clip(random.gauss(0.7, 0.15), 0.3, 1.0),
            life_events_impact=life_events_impact
        )
    
    def simulate_question_response(self, topic: str, difficulty: float, 
                                 daily_state: DailyState, session_fatigue: float,
                                 current_stress: float) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Simulate realistic response to a single question
        
        Returns: (is_correct, response_time_ms, behavioral_data)
        """
        
        # Base success probability from knowledge state
        knowledge_level = self.knowledge_state.get(topic, 0.1)
        base_success_prob = max(0.05, min(0.95, knowledge_level - difficulty * 0.3))
        
        # Personality adjustments
        if self.profile.learning_style == LearningStyle.VISUAL and "geometry" in topic:
            base_success_prob *= 1.1  # Visual learners better at geometry
        
        # Daily state impacts
        mood_factor = 0.8 + daily_state.mood * 0.4  # Mood affects performance
        energy_factor = 0.7 + daily_state.energy_level * 0.3
        fatigue_penalty = 1.0 - session_fatigue * 0.3
        stress_penalty = 1.0 - current_stress * 0.2
        
        # Calculate final success probability
        final_success_prob = base_success_prob * mood_factor * energy_factor * fatigue_penalty * stress_penalty
        final_success_prob = np.clip(final_success_prob, 0.05, 0.95)
        
        is_correct = random.random() < final_success_prob
        
        # Realistic response time modeling
        base_time = 2000  # 2 seconds baseline
        
        # Difficulty affects time
        difficulty_time_factor = 1.0 + difficulty * 0.8
        
        # Individual differences
        processing_speed_factor = 1.0 / self.profile.processing_speed
        
        # State-based time variations
        fatigue_time_penalty = 1.0 + session_fatigue * 0.5
        stress_time_penalty = 1.0 + current_stress * 0.3
        mood_time_factor = 2.0 - daily_state.mood  # Better mood = faster
        
        # Personality factors
        if self.profile.perfectionism_level > 0.7:
            perfectionism_delay = 1.2  # Perfectionists take longer
        else:
            perfectionism_delay = 1.0
            
        # Calculate response time with realistic variation
        mean_time = (base_time * difficulty_time_factor * processing_speed_factor * 
                    fatigue_time_penalty * stress_time_penalty * mood_time_factor * 
                    perfectionism_delay)
        
        # Add log-normal distribution for realistic response time variation
        response_time = max(500, lognorm.rvs(s=0.3, scale=mean_time))
        
        # Generate behavioral indicators
        behavioral_data = {
            'hesitation_ms': max(0, random.gauss(current_stress * 1000, 300)),
            'keystroke_deviation': np.clip(current_stress + random.gauss(0, 0.1), 0, 1),
            'mouse_movement_erratic': current_stress > 0.5,
            'multiple_attempts': not is_correct and random.random() < 0.3,
            'help_requested': not is_correct and random.random() < self.profile.help_seeking_tendency
        }
        
        return is_correct, response_time, behavioral_data
    
    def update_knowledge_state(self, topic: str, is_correct: bool, difficulty: float):
        """Update knowledge state based on BKT-like learning"""
        current_mastery = self.knowledge_state.get(topic, 0.1)
        
        if is_correct:
            # Learning occurred
            learning_rate = 0.1 * (1 - current_mastery)  # Diminishing returns
            learning_rate *= (1 + difficulty * 0.2)  # Harder questions teach more
            self.knowledge_state[topic] = min(0.95, current_mastery + learning_rate)
        else:
            # Small negative impact from failure
            self.knowledge_state[topic] = max(0.05, current_mastery - 0.02)
    
    def apply_forgetting_curve(self, days_since_last_practice: int, topic: str):
        """Apply realistic forgetting based on Ebbinghaus curve"""
        if days_since_last_practice > 0:
            # Exponential decay with individual differences
            decay_rate = 0.1 * (1 - self.profile.conscientiousness * 0.3)  # Conscientious people forget less
            forgetting_factor = math.exp(-decay_rate * days_since_last_practice)
            
            current_mastery = self.knowledge_state.get(topic, 0.1)
            # Never drop below 20% of original knowledge
            min_retention = current_mastery * 0.2
            new_mastery = max(min_retention, current_mastery * forgetting_factor)
            self.knowledge_state[topic] = new_mastery
    
    def simulate_learning_session(self, day: int, daily_state: DailyState,
                                target_questions: int = 15) -> LearningSession:
        """Simulate a complete learning session with realistic behavior"""
        
        session_id = f"{self.student_id}_session_{day}"
        start_time = datetime.now() + timedelta(days=day, hours=random.randint(14, 20))
        
        # Session-level variables
        current_fatigue = 0.0
        current_stress = daily_state.stress_baseline
        questions_attempted = 0
        questions_correct = 0
        response_times = []
        stress_levels = []
        topics_covered = []
        break_requests = 0
        help_requests = 0
        mastery_gains = {}
        
        # Determine session length based on personality and daily state
        base_session_length = 60  # minutes
        personality_modifier = self.profile.conscientiousness * 0.5 + daily_state.motivation * 0.3
        max_session_length = base_session_length * (0.7 + personality_modifier)
        
        session_start_time = datetime.now()
        
        while questions_attempted < target_questions and current_fatigue < 0.8:
            # Select topic (prefer weaker topics but with some randomness)
            topic_weights = [1.0 / (mastery + 0.1) for mastery in 
                           [self.knowledge_state.get(topic, 0.1) for topic in self.topics]]
            topic = np.random.choice(self.topics, p=np.array(topic_weights) / sum(topic_weights))
            
            # Determine question difficulty based on current mastery
            current_mastery = self.knowledge_state.get(topic, 0.1)
            optimal_difficulty = current_mastery + 0.1  # Slight challenge
            difficulty = np.clip(random.gauss(optimal_difficulty, 0.15), 0.1, 0.9)
            
            # Simulate question response
            is_correct, response_time, behavioral_data = self.simulate_question_response(
                topic, difficulty, daily_state, current_fatigue, current_stress
            )
            
            # Update counters
            questions_attempted += 1
            if is_correct:
                questions_correct += 1
            
            response_times.append(response_time)
            stress_levels.append(current_stress)
            
            if topic not in topics_covered:
                topics_covered.append(topic)
            
            # Track behavioral requests
            if behavioral_data.get('help_requested'):
                help_requests += 1
                
            # Update knowledge state
            old_mastery = self.knowledge_state.get(topic, 0.1)
            self.update_knowledge_state(topic, is_correct, difficulty)
            new_mastery = self.knowledge_state.get(topic, 0.1)
            mastery_gains[topic] = mastery_gains.get(topic, 0.0) + (new_mastery - old_mastery)
            
            # Update session state
            current_fatigue += 0.03 + random.uniform(0, 0.02)  # Gradual fatigue
            
            # Stress accumulation based on performance
            if not is_correct:
                stress_increase = 0.05 * (1 + self.profile.neuroticism)
                current_stress = min(0.9, current_stress + stress_increase)
            else:
                # Slight stress reduction from success
                current_stress = max(daily_state.stress_baseline, current_stress - 0.01)
            
            # Check for break requests
            if (current_fatigue > 0.6 and random.random() < 0.3) or current_stress > 0.7:
                break_requests += 1
                current_fatigue *= 0.8  # Break helps with fatigue
                current_stress *= 0.9   # Break helps with stress
                
            # Early session termination due to high stress or fatigue
            if current_stress > 0.8 or current_fatigue > 0.9:
                break
                
            # Natural variation in session length
            elapsed_minutes = (datetime.now() - session_start_time).total_seconds() / 60
            if elapsed_minutes > max_session_length:
                break
        
        # Calculate session metrics
        accuracy = questions_correct / max(questions_attempted, 1)
        avg_response_time = np.mean(response_times) if response_times else 2000
        peak_stress = max(stress_levels) if stress_levels else daily_state.stress_baseline
        
        # Engagement score based on multiple factors
        engagement_score = np.clip(
            daily_state.motivation * 0.4 +
            (1 - current_fatigue) * 0.3 + 
            accuracy * 0.2 +
            (1 - peak_stress) * 0.1,
            0.0, 1.0
        )
        
        session_duration = (datetime.now() - session_start_time).total_seconds() / 60
        
        return LearningSession(
            session_id=session_id,
            date=daily_state.date,
            start_time=start_time,
            duration_minutes=session_duration,
            questions_attempted=questions_attempted,
            questions_correct=questions_correct,
            topics_covered=topics_covered,
            avg_response_time_ms=avg_response_time,
            peak_stress_level=peak_stress,
            final_fatigue_level=current_fatigue,
            break_requests=break_requests,
            help_requests=help_requests,
            mastery_gains=mastery_gains,
            engagement_score=engagement_score
        )
    
    def simulate_3_month_journey(self, start_date: datetime = None) -> Dict[str, Any]:
        """
        Simulate complete 3-month learning journey with realistic human behavior
        
        Returns comprehensive analysis of the learning journey
        """
        if start_date is None:
            start_date = datetime.now()
            
        logger.info(f"Starting 3-month simulation for student {self.student_id}")
        
        # Track various metrics over time
        daily_states = []
        learning_sessions = []
        weekly_summaries = []
        
        # Simulate each day
        for day in range(90):  # 3 months = ~90 days
            daily_state = self.generate_daily_state(day, self.profile)
            daily_states.append(daily_state)
            
            # Apply forgetting for topics not practiced recently
            for topic in self.topics:
                days_since_practice = self._days_since_last_practice(topic, day)
                if days_since_practice > 0:
                    self.apply_forgetting_curve(days_since_practice, topic)
            
            # Decide if student studies today (based on personality and state)
            study_probability = (
                daily_state.motivation * 0.4 +
                self.profile.conscientiousness * 0.4 +
                daily_state.energy_level * 0.2
            )
            
            # Weekend effect (less likely to study)
            if day % 7 in [5, 6]:  # Weekend
                study_probability *= 0.6
                
            if random.random() < study_probability:
                # Determine number of questions based on available time and motivation
                base_questions = 15
                motivation_factor = daily_state.motivation
                energy_factor = daily_state.energy_level
                
                target_questions = int(base_questions * motivation_factor * energy_factor)
                target_questions = max(5, min(30, target_questions))  # Reasonable bounds
                
                session = self.simulate_learning_session(day, daily_state, target_questions)
                learning_sessions.append(session)
                
                # Update tracking
                self.motivation_trend.append(daily_state.motivation)
                self.stress_trend.append(session.peak_stress_level)
            
            # Weekly summary
            if day % 7 == 6:  # End of week
                week_sessions = [s for s in learning_sessions if s.date >= start_date + timedelta(days=day-6)]
                weekly_summary = self._create_weekly_summary(week_sessions, day // 7 + 1)
                weekly_summaries.append(weekly_summary)
        
        # Generate comprehensive analysis
        analysis = self._generate_comprehensive_analysis(
            daily_states, learning_sessions, weekly_summaries, start_date
        )
        
        logger.info(f"Completed 3-month simulation for student {self.student_id}")
        return analysis
    
    def _days_since_last_practice(self, topic: str, current_day: int) -> int:
        """Calculate days since topic was last practiced"""
        # Look through recent learning sessions for this topic
        for session in reversed(self.learning_history[-10:]):  # Check last 10 sessions
            if topic in session.topics_covered:
                # Calculate days difference (simplified)
                return max(0, current_day - len(self.learning_history))
        return current_day  # Never practiced
    
    def _create_weekly_summary(self, week_sessions: List[LearningSession], week_num: int) -> Dict[str, Any]:
        """Create weekly learning summary"""
        if not week_sessions:
            return {
                'week_number': week_num,
                'sessions_completed': 0,
                'total_questions': 0,
                'average_accuracy': 0.0,
                'average_engagement': 0.0,
                'stress_incidents': 0
            }
        
        total_questions = sum(s.questions_attempted for s in week_sessions)
        total_correct = sum(s.questions_correct for s in week_sessions)
        
        return {
            'week_number': week_num,
            'sessions_completed': len(week_sessions),
            'total_questions': total_questions,
            'average_accuracy': total_correct / max(total_questions, 1),
            'average_engagement': np.mean([s.engagement_score for s in week_sessions]),
            'stress_incidents': sum(1 for s in week_sessions if s.peak_stress_level > 0.7),
            'break_requests': sum(s.break_requests for s in week_sessions),
            'help_requests': sum(s.help_requests for s in week_sessions)
        }
    
    def _generate_comprehensive_analysis(self, daily_states: List[DailyState],
                                       learning_sessions: List[LearningSession],
                                       weekly_summaries: List[Dict[str, Any]],
                                       start_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive analysis of the 3-month learning journey"""
        
        # Overall statistics
        total_sessions = len(learning_sessions)
        total_questions = sum(s.questions_attempted for s in learning_sessions)
        total_correct = sum(s.questions_correct for s in learning_sessions)
        overall_accuracy = total_correct / max(total_questions, 1)
        
        # Knowledge progression analysis
        knowledge_progression = {}
        for topic in self.topics:
            initial_mastery = 0.1  # Assumed initial state
            final_mastery = self.knowledge_state[topic]
            knowledge_progression[topic] = {
                'initial_mastery': initial_mastery,
                'final_mastery': final_mastery,
                'improvement': final_mastery - initial_mastery
            }
        
        # Behavioral pattern analysis
        avg_session_length = np.mean([s.duration_minutes for s in learning_sessions])
        stress_pattern = np.mean([s.peak_stress_level for s in learning_sessions])
        engagement_pattern = np.mean([s.engagement_score for s in learning_sessions])
        
        # Learning efficiency metrics
        questions_per_minute = total_questions / sum(s.duration_minutes for s in learning_sessions)
        learning_velocity = sum(sum(gains.values()) for gains in 
                              [s.mastery_gains for s in learning_sessions]) / max(total_sessions, 1)
        
        return {
            'student_id': self.student_id,
            'simulation_period': '90_days',
            'personality_profile': {
                'conscientiousness': self.profile.conscientiousness,
                'neuroticism': self.profile.neuroticism,
                'learning_style': self.profile.learning_style.value,
                'stress_tolerance': self.profile.stress_tolerance
            },
            'overall_statistics': {
                'total_sessions': total_sessions,
                'total_questions_attempted': total_questions,
                'overall_accuracy': round(overall_accuracy, 3),
                'average_session_length_minutes': round(avg_session_length, 1),
                'total_study_hours': round(sum(s.duration_minutes for s in learning_sessions) / 60, 1)
            },
            'knowledge_progression': knowledge_progression,
            'behavioral_patterns': {
                'average_stress_level': round(stress_pattern, 3),
                'average_engagement_score': round(engagement_pattern, 3),
                'questions_per_minute': round(questions_per_minute, 2),
                'learning_velocity': round(learning_velocity, 4),
                'total_break_requests': sum(s.break_requests for s in learning_sessions),
                'total_help_requests': sum(s.help_requests for s in learning_sessions)
            },
            'weekly_summaries': weekly_summaries,
            'daily_mood_trend': [ds.mood for ds in daily_states],
            'motivation_trend': self.motivation_trend,
            'stress_trend': self.stress_trend,
            'final_knowledge_state': self.knowledge_state,
            'simulation_metadata': {
                'start_date': start_date.isoformat(),
                'end_date': (start_date + timedelta(days=89)).isoformat(),
                'total_simulation_days': 90,
                'active_study_days': total_sessions
            }
        }

def create_diverse_student_cohort() -> List[Tuple[str, PsychologicalProfile]]:
    """Create a diverse cohort of students with different psychological profiles"""
    
    students = []
    
    # Student 1: High-achieving, conscientious but anxiety-prone
    profile1 = PsychologicalProfile(
        conscientiousness=0.85,
        neuroticism=0.7,
        openness=0.6,
        processing_speed=1.2,
        stress_tolerance=0.4,
        perfectionism_level=0.8,
        learning_style=LearningStyle.READING_WRITING,
        reading_speed_wpm=320,
        math_anxiety_level=0.4
    )
    students.append(("perfectionist_achiever", profile1))
    
    # Student 2: Laid-back, lower conscientiousness but high confidence
    profile2 = PsychologicalProfile(
        conscientiousness=0.3,
        neuroticism=0.2,
        extraversion=0.8,
        processing_speed=0.9,
        stress_tolerance=0.8,
        impulsiveness=0.7,
        learning_style=LearningStyle.KINESTHETIC,
        reading_speed_wpm=180,
        help_seeking_tendency=0.7
    )
    students.append(("relaxed_social", profile2))
    
    # Student 3: Balanced learner with moderate characteristics
    profile3 = PsychologicalProfile(
        conscientiousness=0.6,
        neuroticism=0.4,
        openness=0.7,
        processing_speed=1.0,
        stress_tolerance=0.6,
        learning_style=LearningStyle.VISUAL,
        reading_speed_wpm=250,
        math_anxiety_level=0.2,
        help_seeking_tendency=0.5
    )
    students.append(("balanced_learner", profile3))
    
    return students

async def run_comprehensive_3_month_simulation():
    """Run comprehensive 3-month simulation for diverse student cohort"""
    
    logger.info("Starting comprehensive 3-month human-like simulation")
    
    # Create diverse student cohort
    student_cohort = create_diverse_student_cohort()
    
    # Run simulations for each student
    simulation_results = {}
    
    for student_type, profile in student_cohort:
        logger.info(f"Running simulation for {student_type}")
        
        simulator = AdvancedHumanSimulator(profile, student_type)
        results = simulator.simulate_3_month_journey()
        
        simulation_results[student_type] = results
        
        # Save individual results
        with open(f'simulation_results_{student_type}.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    # Generate comparative analysis
    comparative_analysis = generate_comparative_analysis(simulation_results)
    
    # Save comprehensive results
    final_results = {
        'individual_results': simulation_results,
        'comparative_analysis': comparative_analysis,
        'simulation_metadata': {
            'total_students': len(student_cohort),
            'simulation_duration_days': 90,
            'simulation_completed': datetime.now().isoformat()
        }
    }
    
    with open('comprehensive_3_month_simulation_results.json', 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    logger.info("Comprehensive 3-month simulation completed")
    return final_results

def generate_comparative_analysis(simulation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comparative analysis across different student types"""
    
    students = list(simulation_results.keys())
    
    # Compare learning outcomes
    learning_outcomes = {}
    for student in students:
        results = simulation_results[student]
        learning_outcomes[student] = {
            'total_improvement': sum(
                prog['improvement'] for prog in results['knowledge_progression'].values()
            ),
            'final_accuracy': results['overall_statistics']['overall_accuracy'],
            'study_efficiency': results['behavioral_patterns']['learning_velocity'],
            'stress_management': 1 - results['behavioral_patterns']['average_stress_level']
        }
    
    # Identify patterns
    patterns = {
        'most_improved': max(students, key=lambda s: learning_outcomes[s]['total_improvement']),
        'most_accurate': max(students, key=lambda s: learning_outcomes[s]['final_accuracy']),
        'most_efficient': max(students, key=lambda s: learning_outcomes[s]['study_efficiency']),
        'best_stress_management': max(students, key=lambda s: learning_outcomes[s]['stress_management'])
    }
    
    return {
        'learning_outcomes_comparison': learning_outcomes,
        'performance_patterns': patterns,
        'insights': [
            "Different personality types show distinct learning patterns",
            "Stress tolerance significantly impacts learning efficiency",
            "Conscientiousness correlates with consistent study habits",
            "Individual differences require personalized approaches"
        ]
    }

if __name__ == "__main__":
    # Run the comprehensive simulation
    results = asyncio.run(run_comprehensive_3_month_simulation())
    print("🎯 3-Month Human-Like Simulation Complete!")
    print(f"📊 Results saved to comprehensive_3_month_simulation_results.json")