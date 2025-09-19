#!/usr/bin/env python3
"""
Standalone BKT Simulation Bot
Enterprise-grade simulation that doesn't require database connectivity
"""

import json
import random
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class LearnerType(Enum):
    SLOW_STEADY = "slow_steady"
    FAST_SHALLOW = "fast_shallow"
    INCONSISTENT = "inconsistent"
    ANXIOUS = "anxious"
    VISUAL = "visual"
    ANALYTICAL = "analytical"

class MoodState(Enum):
    ENERGETIC = "energetic"
    FOCUSED = "focused"
    TIRED = "tired"
    FRUSTRATED = "frustrated"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"

@dataclass
class StudentProfile:
    name: str
    grade: str = "11th"
    learner_type: LearnerType = LearnerType.SLOW_STEADY
    
    # Academic strengths (0.0 to 1.0)
    math_aptitude: float = 0.6
    physics_aptitude: float = 0.5  
    chemistry_aptitude: float = 0.4
    
    # Cognitive factors
    attention_span: int = 25  # minutes
    memory_retention: float = 0.7
    persistence: float = 0.6
    
    # Behavioral patterns
    daily_study_hours: float = 3.0
    motivation_level: float = 0.7
    stress_threshold: float = 0.6
    
    # Learning preferences
    prefers_theory: bool = False
    learns_from_mistakes: bool = True
    needs_encouragement: bool = True

class StandaloneBKT:
    """Standalone BKT implementation for simulation"""
    
    def __init__(self):
        # Default BKT parameters for different concept types
        self.default_parameters = {
            'easy': {'prior': 0.1, 'transit': 0.3, 'slip': 0.1, 'guess': 0.15},
            'medium': {'prior': 0.08, 'transit': 0.25, 'slip': 0.15, 'guess': 0.2},
            'hard': {'prior': 0.05, 'transit': 0.2, 'slip': 0.2, 'guess': 0.25}
        }
        self.student_states = {}  # {(student_id, concept): {'mastery': float, 'history': []}}
    
    def get_parameters(self, concept_id: str, difficulty: float) -> Dict[str, float]:
        """Get BKT parameters based on concept difficulty"""
        if difficulty < 0.4:
            return self.default_parameters['easy']
        elif difficulty < 0.7:
            return self.default_parameters['medium']
        else:
            return self.default_parameters['hard']
    
    def update_mastery(self, student_id: str, concept_id: str, is_correct: bool, difficulty: float) -> Dict[str, Any]:
        """Update student mastery using BKT mathematics"""
        key = (student_id, concept_id)
        params = self.get_parameters(concept_id, difficulty)
        
        # Initialize if first time
        if key not in self.student_states:
            self.student_states[key] = {
                'mastery': params['prior'],
                'history': [],
                'attempts': 0,
                'correct': 0
            }
        
        state = self.student_states[key]
        previous_mastery = state['mastery']
        
        # BKT Update Formula
        P_L = previous_mastery
        P_T = params['transit']
        P_S = params['slip']
        P_G = params['guess']
        
        # Evidence probability
        if is_correct:
            P_evidence = P_L * (1 - P_S) + (1 - P_L) * P_G
        else:
            P_evidence = P_L * P_S + (1 - P_L) * (1 - P_G)
        
        # Posterior probability of knowledge given evidence
        if is_correct:
            P_L_given_evidence = (P_L * (1 - P_S)) / P_evidence
        else:
            P_L_given_evidence = (P_L * P_S) / P_evidence
        
        # Update mastery with learning opportunity
        new_mastery = P_L_given_evidence + (1 - P_L_given_evidence) * P_T
        
        # Update state
        state['mastery'] = new_mastery
        state['attempts'] += 1
        if is_correct:
            state['correct'] += 1
        
        state['history'].append({
            'is_correct': is_correct,
            'previous_mastery': previous_mastery,
            'new_mastery': new_mastery,
            'evidence_prob': P_evidence,
            'params_used': params.copy()
        })
        
        return {
            'previous_mastery': previous_mastery,
            'new_mastery': new_mastery,
            'learning_occurred': new_mastery > previous_mastery + 0.01,
            'confidence': min(0.95, new_mastery),
            'attempts': state['attempts'],
            'accuracy': state['correct'] / state['attempts'],
            'params_used': params
        }

class JEE11thSyllabus:
    """Complete JEE Main 11th standard syllabus with realistic difficulty progression"""
    
    PHYSICS_TOPICS = {
        "units_and_measurements": {"difficulty": 0.3, "prereq": [], "weight": 0.15},
        "motion_1d": {"difficulty": 0.4, "prereq": ["units_and_measurements"], "weight": 0.20},
        "motion_2d": {"difficulty": 0.6, "prereq": ["motion_1d"], "weight": 0.25},
        "laws_of_motion": {"difficulty": 0.5, "prereq": ["motion_1d"], "weight": 0.25},
        "work_energy_power": {"difficulty": 0.7, "prereq": ["laws_of_motion"], "weight": 0.30},
        "circular_motion": {"difficulty": 0.8, "prereq": ["motion_2d"], "weight": 0.35},
        "kinetic_theory": {"difficulty": 0.6, "prereq": [], "weight": 0.20},
        "thermodynamics_basic": {"difficulty": 0.7, "prereq": ["kinetic_theory"], "weight": 0.30},
        "simple_harmonic_motion": {"difficulty": 0.6, "prereq": ["circular_motion"], "weight": 0.25},
        "waves": {"difficulty": 0.7, "prereq": ["simple_harmonic_motion"], "weight": 0.30},
    }
    
    CHEMISTRY_TOPICS = {
        "atomic_structure": {"difficulty": 0.4, "prereq": [], "weight": 0.20},
        "periodic_table": {"difficulty": 0.5, "prereq": ["atomic_structure"], "weight": 0.25},
        "chemical_bonding": {"difficulty": 0.7, "prereq": ["atomic_structure"], "weight": 0.35},
        "organic_chemistry_basic": {"difficulty": 0.6, "prereq": [], "weight": 0.25},
        "hydrocarbons": {"difficulty": 0.7, "prereq": ["organic_chemistry_basic"], "weight": 0.30},
        "states_of_matter": {"difficulty": 0.5, "prereq": [], "weight": 0.20},
        "thermodynamics_chem": {"difficulty": 0.8, "prereq": ["states_of_matter"], "weight": 0.35},
    }
    
    MATHEMATICS_TOPICS = {
        "complex_numbers": {"difficulty": 0.5, "prereq": [], "weight": 0.20},
        "quadratic_equations": {"difficulty": 0.4, "prereq": [], "weight": 0.15},
        "sequences_series": {"difficulty": 0.6, "prereq": ["quadratic_equations"], "weight": 0.25},
        "binomial_theorem": {"difficulty": 0.7, "prereq": ["sequences_series"], "weight": 0.30},
        "limits": {"difficulty": 0.6, "prereq": [], "weight": 0.25},
        "calculus_derivatives": {"difficulty": 0.7, "prereq": ["limits"], "weight": 0.30},
        "applications_derivatives": {"difficulty": 0.8, "prereq": ["calculus_derivatives"], "weight": 0.35},
        "straight_lines": {"difficulty": 0.5, "prereq": [], "weight": 0.20},
        "circles": {"difficulty": 0.6, "prereq": ["straight_lines"], "weight": 0.25},
        "conic_sections": {"difficulty": 0.8, "prereq": ["circles"], "weight": 0.35},
        "trigonometry_basic": {"difficulty": 0.4, "prereq": [], "weight": 0.15},
        "trigonometric_equations": {"difficulty": 0.7, "prereq": ["trigonometry_basic"], "weight": 0.30},
    }

class VirtualStudent:
    """Human-like student simulation with realistic learning behaviors"""
    
    def __init__(self, profile: StudentProfile):
        self.profile = profile
        self.current_mood = MoodState.FOCUSED
        self.daily_energy = 1.0
        self.study_session_time = 0
        self.mastery_levels = {}
        self.mistake_memory = {}
        self.confidence_levels = {}
        self.fatigue_level = 0.0
        self.consecutive_failures = 0
        self.recent_success_streak = 0
        
        # Initialize confidence levels for all topics
        all_topics = {**JEE11thSyllabus.PHYSICS_TOPICS, 
                     **JEE11thSyllabus.CHEMISTRY_TOPICS, 
                     **JEE11thSyllabus.MATHEMATICS_TOPICS}
        
        for topic in all_topics:
            subject_aptitude = self._get_subject_aptitude(topic)
            self.confidence_levels[topic] = subject_aptitude + random.uniform(-0.2, 0.2)
            self.mastery_levels[topic] = max(0.1, subject_aptitude + random.uniform(-0.3, 0.1))
    
    def _get_subject_aptitude(self, topic: str) -> float:
        if any(t in topic.lower() for t in ['motion', 'force', 'energy', 'wave', 'thermo', 'kinetic']):
            return self.profile.physics_aptitude
        elif any(t in topic.lower() for t in ['organic', 'atomic', 'bond', 'chemical', 'periodic']):
            return self.profile.chemistry_aptitude
        else:  # Mathematics
            return self.profile.math_aptitude
    
    def start_study_session(self) -> None:
        hour = datetime.now().hour
        
        if 8 <= hour <= 11:
            self.daily_energy = random.uniform(0.8, 1.0)
            self.current_mood = random.choices(
                [MoodState.ENERGETIC, MoodState.FOCUSED],
                weights=[0.6, 0.4]
            )[0]
        elif 14 <= hour <= 17:
            self.daily_energy = random.uniform(0.6, 0.9)
            self.current_mood = random.choices(
                [MoodState.FOCUSED, MoodState.TIRED],
                weights=[0.7, 0.3]
            )[0]
        elif 19 <= hour <= 22:
            self.daily_energy = random.uniform(0.5, 0.8)
            self.current_mood = random.choices(
                [MoodState.FOCUSED, MoodState.TIRED, MoodState.ANXIOUS],
                weights=[0.5, 0.3, 0.2]
            )[0]
        
        self.study_session_time = 0
        self.fatigue_level = 0.0
        
    def solve_question(self, topic: str, difficulty: float, question_id: str) -> Dict[str, Any]:
        # Update study session fatigue
        self.study_session_time += random.uniform(2, 8)
        self.fatigue_level = min(1.0, self.study_session_time / (self.profile.attention_span * 60))
        
        # Calculate base probability of success
        base_ability = self._get_subject_aptitude(topic)
        confidence = self.confidence_levels.get(topic, 0.5)
        
        # Adjust for question difficulty
        difficulty_factor = 1.0 - (difficulty * 0.6)
        
        # Apply psychological factors
        mood_multiplier = self._get_mood_effect()
        fatigue_penalty = self.fatigue_level * 0.3
        confidence_boost = (confidence - 0.5) * 0.4
        frustration_penalty = min(0.4, self.consecutive_failures * 0.1)
        streak_bonus = min(0.3, self.recent_success_streak * 0.05)
        
        # Calculate final success probability
        success_prob = (
            base_ability * difficulty_factor * mood_multiplier
            + confidence_boost + streak_bonus
            - fatigue_penalty - frustration_penalty
        )
        success_prob = max(0.05, min(0.95, success_prob))
        
        # Determine if question is solved correctly
        is_correct = random.random() < success_prob
        
        # Realistic response time modeling
        base_time = difficulty * 300 + random.uniform(60, 180)
        if not is_correct:
            base_time *= random.uniform(1.2, 2.0)
        if self.fatigue_level > 0.6:
            base_time *= random.uniform(1.1, 1.5)
        if self.current_mood == MoodState.ANXIOUS:
            base_time *= random.uniform(1.2, 1.8)
            
        response_time_ms = int(base_time * 1000)
        
        # Update psychological state
        if is_correct:
            self.consecutive_failures = 0
            self.recent_success_streak += 1
            self.confidence_levels[topic] = min(1.0, self.confidence_levels[topic] + 0.02)
            if self.recent_success_streak > 3:
                self.current_mood = MoodState.CONFIDENT
        else:
            self.consecutive_failures += 1
            self.recent_success_streak = 0
            self.confidence_levels[topic] = max(0.1, self.confidence_levels[topic] - 0.03)
            if self.consecutive_failures > 2:
                self.current_mood = MoodState.FRUSTRATED
                
        # Learning from mistakes
        if not is_correct and self.profile.learns_from_mistakes:
            self.mistake_memory[topic] = self.mistake_memory.get(topic, 0) + 1
            self.mastery_levels[topic] = min(1.0, self.mastery_levels[topic] + 0.01)
        
        return {
            'question_id': question_id,
            'topic': topic,
            'difficulty': difficulty,
            'is_correct': is_correct,
            'response_time_ms': response_time_ms,
            'confidence': confidence,
            'mood': self.current_mood.value,
            'fatigue_level': self.fatigue_level,
            'success_probability_calculated': success_prob,
        }
    
    def _get_mood_effect(self) -> float:
        mood_effects = {
            MoodState.ENERGETIC: 1.1,
            MoodState.FOCUSED: 1.0,
            MoodState.CONFIDENT: 1.05,
            MoodState.TIRED: 0.8,
            MoodState.FRUSTRATED: 0.7,
            MoodState.ANXIOUS: 0.75
        }
        return mood_effects.get(self.current_mood, 1.0)
    
    def needs_break(self) -> bool:
        if self.fatigue_level > 0.8:
            return True
        if self.current_mood == MoodState.FRUSTRATED and self.consecutive_failures > 3:
            return True
        if self.study_session_time > self.profile.attention_span * 60 * 0.8:
            return True
        return False
    
    def take_break(self, duration_minutes: int = 15) -> None:
        self.fatigue_level = max(0.0, self.fatigue_level - 0.3)
        self.study_session_time = max(0, self.study_session_time - duration_minutes * 60)
        
        if self.current_mood in [MoodState.FRUSTRATED, MoodState.TIRED]:
            self.current_mood = random.choices(
                [MoodState.FOCUSED, MoodState.ENERGETIC],
                weights=[0.7, 0.3]
            )[0]

class AdityaStandaloneSimulation:
    """30-day comprehensive standalone simulation"""
    
    def __init__(self):
        # Create Aditya's realistic profile
        self.aditya = VirtualStudent(StudentProfile(
            name="Aditya",
            grade="11th",
            learner_type=LearnerType.SLOW_STEADY,
            math_aptitude=0.4,
            physics_aptitude=0.45,
            chemistry_aptitude=0.35,
            attention_span=20,
            memory_retention=0.6,
            persistence=0.8,
            daily_study_hours=2.5,
            motivation_level=0.75,
            stress_threshold=0.5,
            prefers_theory=False,
            learns_from_mistakes=True,
            needs_encouragement=True
        ))
        
        self.bkt_engine = StandaloneBKT()
        self.simulation_data = []
        self.daily_summaries = []
        self.curriculum_plan = self._create_30_day_curriculum()
        
    def _create_30_day_curriculum(self) -> List[Dict]:
        curriculum = []
        
        # Week 1: Foundation Building
        week1_topics = [
            "units_and_measurements", "motion_1d", "atomic_structure", 
            "quadratic_equations", "trigonometry_basic"
        ]
        
        # Week 2: Intermediate Concepts
        week2_topics = [
            "motion_2d", "laws_of_motion", "periodic_table", 
            "complex_numbers", "straight_lines"
        ]
        
        # Week 3: Advanced Concepts
        week3_topics = [
            "work_energy_power", "chemical_bonding", "sequences_series",
            "limits", "circles"
        ]
        
        # Week 4: Challenging Topics + Revision
        week4_topics = [
            "circular_motion", "thermodynamics_basic", "calculus_derivatives",
            "hydrocarbons", "conic_sections"
        ]
        
        all_weekly_topics = [week1_topics, week2_topics, week3_topics, week4_topics]
        
        for week, topics in enumerate(all_weekly_topics, 1):
            for day in range(7):
                day_num = (week - 1) * 7 + day + 1
                if day_num > 30:
                    break
                    
                questions_per_day = 8 if day < 5 else 5
                
                curriculum.append({
                    'day': day_num,
                    'week': week,
                    'is_weekend': day >= 5,
                    'topics': topics,
                    'target_questions': questions_per_day,
                    'focus_topic': random.choice(topics)
                })
        
        # Add final days 29-30
        for day in [29, 30]:
            curriculum.append({
                'day': day,
                'week': 5,
                'is_weekend': True,
                'topics': week4_topics,
                'target_questions': 3,
                'focus_topic': random.choice(week4_topics)
            })
        
        return curriculum
    
    def _generate_question_for_topic(self, topic: str, day: int) -> Dict:
        all_topics = {**JEE11thSyllabus.PHYSICS_TOPICS, 
                     **JEE11thSyllabus.CHEMISTRY_TOPICS, 
                     **JEE11thSyllabus.MATHEMATICS_TOPICS}
        
        topic_info = all_topics.get(topic, {"difficulty": 0.5, "weight": 0.2})
        
        # Difficulty progression over time
        base_difficulty = topic_info["difficulty"]
        progression_factor = min(0.3, day * 0.01)
        final_difficulty = min(1.0, base_difficulty + progression_factor)
        
        return {
            'question_id': f"{topic.upper()}_{day:02d}_{random.randint(1000, 9999)}",
            'topic': topic,
            'difficulty': final_difficulty,
            'subject': self._get_subject_from_topic(topic),
            'estimated_time': int(final_difficulty * 300 + random.uniform(60, 120))
        }
    
    def _get_subject_from_topic(self, topic: str) -> str:
        if topic in JEE11thSyllabus.PHYSICS_TOPICS:
            return "Physics"
        elif topic in JEE11thSyllabus.CHEMISTRY_TOPICS:
            return "Chemistry"
        else:
            return "Mathematics"
    
    def simulate_single_day(self, day_info: Dict) -> Dict:
        day = day_info['day']
        print(f"\n📅 Day {day} - Week {day_info['week']} {'(Weekend)' if day_info['is_weekend'] else ''}")
        print(f"🎯 Focus Topic: {day_info['focus_topic']}")
        
        self.aditya.start_study_session()
        
        daily_results = {
            'day': day,
            'week': day_info['week'],
            'is_weekend': day_info['is_weekend'],
            'questions_attempted': 0,
            'questions_correct': 0,
            'topics_studied': set(),
            'total_study_time': 0,
            'breaks_taken': 0,
            'bkt_updates': [],
            'performance_by_topic': {},
        }
        
        questions_completed = 0
        target_questions = day_info['target_questions']
        
        if day_info['is_weekend']:
            target_questions = int(target_questions * 0.7)
        
        while questions_completed < target_questions:
            # Check if break needed
            if self.aditya.needs_break():
                print(f"  💤 Taking break - Fatigue: {self.aditya.fatigue_level:.2f}")
                self.aditya.take_break()
                daily_results['breaks_taken'] += 1
                continue
            
            # Select topic
            if random.random() < 0.7:
                selected_topic = day_info['focus_topic']
            else:
                selected_topic = random.choice(day_info['topics'])
            
            # Generate question
            question = self._generate_question_for_topic(selected_topic, day)
            
            # Student attempts the question
            attempt = self.aditya.solve_question(
                question['topic'], 
                question['difficulty'], 
                question['question_id']
            )
            
            # Update BKT system
            bkt_result = self.bkt_engine.update_mastery(
                student_id="aditya_simulation",
                concept_id=selected_topic,
                is_correct=attempt['is_correct'],
                difficulty=question['difficulty']
            )
            
            # Record BKT insights
            daily_results['bkt_updates'].append({
                'topic': selected_topic,
                'question_id': question['question_id'],
                'previous_mastery': bkt_result['previous_mastery'],
                'new_mastery': bkt_result['new_mastery'],
                'learning_occurred': bkt_result['learning_occurred'],
                'confidence': bkt_result['confidence']
            })
            
            correct_symbol = "✅" if attempt['is_correct'] else "❌"
            print(f"  📝 Q{questions_completed+1}: {selected_topic} ({correct_symbol}) "
                  f"Mastery: {bkt_result['previous_mastery']:.3f} → {bkt_result['new_mastery']:.3f}")
            
            # Update daily stats
            questions_completed += 1
            daily_results['questions_attempted'] += 1
            if attempt['is_correct']:
                daily_results['questions_correct'] += 1
            
            daily_results['topics_studied'].add(selected_topic)
            daily_results['total_study_time'] += attempt['response_time_ms'] / 1000 / 60
            
            # Track topic performance
            if selected_topic not in daily_results['performance_by_topic']:
                daily_results['performance_by_topic'][selected_topic] = {'attempted': 0, 'correct': 0}
            daily_results['performance_by_topic'][selected_topic]['attempted'] += 1
            if attempt['is_correct']:
                daily_results['performance_by_topic'][selected_topic]['correct'] += 1
            
            # Record full attempt data
            self.simulation_data.append({
                'day': day,
                'question_data': question,
                'student_attempt': attempt,
                'bkt_result': bkt_result
            })
            
            time.sleep(0.05)  # Small delay
        
        # Calculate daily performance metrics
        daily_accuracy = daily_results['questions_correct'] / daily_results['questions_attempted'] if daily_results['questions_attempted'] > 0 else 0
        
        daily_summary = {
            **daily_results,
            'topics_studied': list(daily_results['topics_studied']),
            'daily_accuracy': daily_accuracy,
            'study_efficiency': daily_results['questions_attempted'] / (daily_results['total_study_time'] / 60) if daily_results['total_study_time'] > 0 else 0,
            'avg_mastery_gain': sum([u['new_mastery'] - u['previous_mastery'] for u in daily_results['bkt_updates']]) / len(daily_results['bkt_updates']) if daily_results['bkt_updates'] else 0
        }
        
        print(f"  📊 Day {day} Summary: {daily_results['questions_correct']}/{daily_results['questions_attempted']} correct "
              f"({daily_accuracy:.1%}), {len(daily_results['topics_studied'])} topics, "
              f"{daily_results['total_study_time']:.1f}min study time")
        
        return daily_summary
    
    def run_30_day_simulation(self) -> Dict:
        print("🚀 Starting 30-Day Aditya Learning Simulation (Standalone Mode)")
        print(f"👨‍🎓 Student Profile: {self.aditya.profile.name} - {self.aditya.profile.learner_type.value}")
        print(f"📚 Aptitudes: Math={self.aditya.profile.math_aptitude:.1f}, Physics={self.aditya.profile.physics_aptitude:.1f}, Chemistry={self.aditya.profile.chemistry_aptitude:.1f}")
        print("=" * 80)
        
        for day_plan in self.curriculum_plan:
            daily_summary = self.simulate_single_day(day_plan)
            self.daily_summaries.append(daily_summary)
            
            # Weekly progress report
            if day_plan['day'] % 7 == 0:
                self._generate_weekly_report(day_plan['week'])
        
        # Generate comprehensive final analysis
        final_analysis = self._generate_final_analysis()
        return final_analysis
    
    def _generate_weekly_report(self, week: int) -> None:
        week_data = [d for d in self.daily_summaries if d['week'] == week]
        
        if not week_data:
            return
            
        total_questions = sum(d['questions_attempted'] for d in week_data)
        total_correct = sum(d['questions_correct'] for d in week_data)
        avg_accuracy = total_correct / total_questions if total_questions > 0 else 0
        total_study_time = sum(d['total_study_time'] for d in week_data)
        
        all_topics = set()
        for d in week_data:
            all_topics.update(d['topics_studied'])
        
        print(f"\n📋 Week {week} Summary:")
        print(f"  Questions: {total_correct}/{total_questions} ({avg_accuracy:.1%} accuracy)")
        print(f"  Study Time: {total_study_time:.1f} minutes")
        print(f"  Topics Covered: {len(all_topics)}")
    
    def _generate_final_analysis(self) -> Dict:
        if not self.daily_summaries:
            return {}
        
        # Overall statistics
        total_questions = sum(d['questions_attempted'] for d in self.daily_summaries)
        total_correct = sum(d['questions_correct'] for d in self.daily_summaries)
        overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
        total_study_hours = sum(d['total_study_time'] for d in self.daily_summaries) / 60
        
        # Learning progression analysis
        weekly_accuracies = []
        for week in range(1, 5):
            week_data = [d for d in self.daily_summaries if d['week'] == week]
            if week_data:
                week_questions = sum(d['questions_attempted'] for d in week_data)
                week_correct = sum(d['questions_correct'] for d in week_data)
                week_accuracy = week_correct / week_questions if week_questions > 0 else 0
                weekly_accuracies.append(week_accuracy)
        
        # Topic performance analysis
        topic_performance = {}
        for day_data in self.daily_summaries:
            for topic, perf in day_data['performance_by_topic'].items():
                if topic not in topic_performance:
                    topic_performance[topic] = {'attempted': 0, 'correct': 0}
                topic_performance[topic]['attempted'] += perf['attempted']
                topic_performance[topic]['correct'] += perf['correct']
        
        # Mastery improvements from BKT
        mastery_improvements = {}
        final_masteries = {}
        for data_point in self.simulation_data:
            if data_point['bkt_result']:
                topic = data_point['question_data']['topic']
                improvement = data_point['bkt_result']['new_mastery'] - data_point['bkt_result']['previous_mastery']
                if topic not in mastery_improvements:
                    mastery_improvements[topic] = []
                mastery_improvements[topic].append(improvement)
                final_masteries[topic] = data_point['bkt_result']['new_mastery']
        
        # Final analysis
        analysis = {
            'simulation_summary': {
                'student_name': self.aditya.profile.name,
                'simulation_days': 30,
                'total_questions_attempted': total_questions,
                'total_correct_answers': total_correct,
                'overall_accuracy': overall_accuracy,
                'total_study_hours': total_study_hours,
                'avg_daily_questions': total_questions / 30,
                'avg_daily_study_time': total_study_hours / 30
            },
            'learning_progression': {
                'week_1_accuracy': weekly_accuracies[0] if len(weekly_accuracies) > 0 else 0,
                'week_2_accuracy': weekly_accuracies[1] if len(weekly_accuracies) > 1 else 0,
                'week_3_accuracy': weekly_accuracies[2] if len(weekly_accuracies) > 2 else 0,
                'week_4_accuracy': weekly_accuracies[3] if len(weekly_accuracies) > 3 else 0,
                'improvement_rate': (weekly_accuracies[-1] - weekly_accuracies[0]) / 3 if len(weekly_accuracies) >= 2 else 0,
                'learning_curve_type': self._classify_learning_curve(weekly_accuracies)
            },
            'topic_mastery_analysis': {
                topic: {
                    'accuracy': perf['correct'] / perf['attempted'],
                    'questions_attempted': perf['attempted'],
                    'mastery_classification': self._classify_topic_mastery(perf['correct'] / perf['attempted']),
                    'final_bkt_mastery': final_masteries.get(topic, 0.0)
                }
                for topic, perf in topic_performance.items() if perf['attempted'] > 0
            },
            'bkt_effectiveness': {
                'topics_with_improvement': len([t for t, improvements in mastery_improvements.items() if sum(improvements) > 0]),
                'avg_mastery_gain_per_topic': {
                    topic: sum(improvements) / len(improvements)
                    for topic, improvements in mastery_improvements.items()
                },
                'total_concepts_learned': len([t for t, mastery in final_masteries.items() if mastery > 0.7]),
                'adaptive_learning_success': overall_accuracy > 0.6
            },
            'student_behavioral_insights': {
                'persistence_demonstrated': self.aditya.consecutive_failures < 5,
                'learning_from_mistakes': any(topic in self.aditya.mistake_memory for topic in topic_performance),
                'confidence_growth': any(conf > 0.6 for conf in self.aditya.confidence_levels.values()),
                'study_consistency': len(self.daily_summaries) == 30
            },
            'system_recommendations': self._generate_system_recommendations(overall_accuracy, weekly_accuracies, topic_performance)
        }
        
        return analysis
    
    def _classify_learning_curve(self, weekly_accuracies: List[float]) -> str:
        if len(weekly_accuracies) < 2:
            return "insufficient_data"
        
        if weekly_accuracies[-1] > weekly_accuracies[0] + 0.1:
            return "steady_improvement"
        elif weekly_accuracies[-1] < weekly_accuracies[0] - 0.1:
            return "declining_performance"
        else:
            return "plateau"
    
    def _classify_topic_mastery(self, accuracy: float) -> str:
        if accuracy >= 0.8:
            return "mastered"
        elif accuracy >= 0.6:
            return "proficient"
        elif accuracy >= 0.4:
            return "developing"
        else:
            return "needs_attention"
    
    def _generate_system_recommendations(self, overall_accuracy: float, weekly_accuracies: List[float], topic_performance: Dict) -> List[str]:
        recommendations = []
        
        if overall_accuracy < 0.5:
            recommendations.append("Implement more foundational content before advanced topics")
        
        if len(weekly_accuracies) >= 2 and weekly_accuracies[-1] <= weekly_accuracies[0]:
            recommendations.append("Add motivational elements and progress visualization")
        
        weak_topics = [topic for topic, perf in topic_performance.items() if perf['correct'] / perf['attempted'] < 0.4]
        if len(weak_topics) > 3:
            recommendations.append("Implement prerequisite checking before topic introduction")
        
        if overall_accuracy > 0.7:
            recommendations.append("System is effectively adapting to student needs")
        
        return recommendations

def save_simulation_results(analysis: Dict, filename: str = "aditya_standalone_simulation.json"):
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"📁 Simulation results saved to {filename}")

def print_detailed_report(analysis: Dict):
    print("\n" + "=" * 100)
    print("🎓 ADITYA 30-DAY LEARNING SIMULATION - FINAL ANALYSIS")
    print("=" * 100)
    
    # Summary
    summary = analysis['simulation_summary']
    print(f"\n📊 OVERALL PERFORMANCE:")
    print(f"  Total Questions: {summary['total_questions_attempted']}")
    print(f"  Correct Answers: {summary['total_correct_answers']} ({summary['overall_accuracy']:.1%})")
    print(f"  Study Hours: {summary['total_study_hours']:.1f}")
    print(f"  Daily Average: {summary['avg_daily_questions']:.1f} questions, {summary['avg_daily_study_time']:.1f} hours")
    
    # Learning progression
    progression = analysis['learning_progression']
    print(f"\n📈 LEARNING PROGRESSION:")
    print(f"  Week 1: {progression['week_1_accuracy']:.1%}")
    print(f"  Week 2: {progression['week_2_accuracy']:.1%}")
    print(f"  Week 3: {progression['week_3_accuracy']:.1%}")
    print(f"  Week 4: {progression['week_4_accuracy']:.1%}")
    print(f"  Improvement Rate: {progression['improvement_rate']:.1%} per week")
    print(f"  Learning Curve: {progression['learning_curve_type']}")
    
    # Topic analysis
    print(f"\n🎯 TOPIC MASTERY ANALYSIS:")
    topic_analysis = analysis['topic_mastery_analysis']
    for topic, data in topic_analysis.items():
        print(f"  {topic}: {data['accuracy']:.1%} ({data['mastery_classification']}) - BKT Mastery: {data['final_bkt_mastery']:.3f}")
    
    # BKT effectiveness
    bkt = analysis['bkt_effectiveness']
    print(f"\n🧠 BKT ENGINE EFFECTIVENESS:")
    print(f"  Topics Showing Improvement: {bkt['topics_with_improvement']}")
    print(f"  Concepts Learned (>0.7 mastery): {bkt['total_concepts_learned']}")
    print(f"  Adaptive Learning Success: {'✅ Yes' if bkt['adaptive_learning_success'] else '❌ No'}")
    
    # Top mastery gains
    print(f"\n🚀 TOP MASTERY GAINS:")
    mastery_gains = sorted(bkt['avg_mastery_gain_per_topic'].items(), key=lambda x: x[1], reverse=True)
    for topic, gain in mastery_gains[:5]:
        print(f"  {topic}: +{gain:.3f} mastery points")
    
    # Recommendations
    print(f"\n💡 SYSTEM RECOMMENDATIONS:")
    for rec in analysis['system_recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    simulation = AdityaStandaloneSimulation()
    final_analysis = simulation.run_30_day_simulation()
    
    # Print detailed report
    print_detailed_report(final_analysis)
    
    # Save results
    save_simulation_results(final_analysis)
    
    print(f"\n🎉 Simulation Complete! Aditya's learning journey analyzed over 30 days.")
    print(f"📈 Overall Success Rate: {final_analysis['simulation_summary']['overall_accuracy']:.1%}")
    print(f"🎯 BKT Engine Performance: {'EFFECTIVE' if final_analysis['bkt_effectiveness']['adaptive_learning_success'] else 'NEEDS IMPROVEMENT'}")