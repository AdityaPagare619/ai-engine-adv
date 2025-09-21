#!/usr/bin/env python3
"""
Enhanced BKT System with Pedagogical Intelligence
Addresses the 5.3% success rate issue with smart teaching methods
Integrates prerequisite knowledge management for improved learning paths
"""

import random
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add the ai_engine source to Python path if not already there
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_engine', 'src'))

# Import prerequisite knowledge management
from ai_engine.src.knowledge_tracing.prerequisite.manager import PrerequisiteManager
from ai_engine.src.knowledge_tracing.prerequisite.dependency_graph import PrerequisiteAnalysisResult

logger = logging.getLogger("enhanced_bkt")

class DifficultyLevel(Enum):
    FOUNDATION = "foundation"      # 0.2-0.4 difficulty
    BUILDING = "building"          # 0.4-0.6 difficulty  
    INTERMEDIATE = "intermediate"  # 0.6-0.7 difficulty
    ADVANCED = "advanced"         # 0.7-0.9 difficulty

class StudentState(Enum):
    STRUGGLING = "struggling"      # <30% accuracy
    LEARNING = "learning"          # 30-60% accuracy
    PROGRESSING = "progressing"    # 60-80% accuracy
    MASTERING = "mastering"        # >80% accuracy

@dataclass
class MotivationalFeedback:
    message: str
    encouragement_level: float  # 0.0 to 1.0
    next_action: str
    prerequisite_suggestion: Optional[Dict[str, Any]] = None

class PedagogicalBKT:
    """Enhanced BKT with teaching intelligence and prerequisite knowledge management"""
    
    def __init__(self, mastery_threshold: float = 0.75):
        # Core BKT parameters (more forgiving for beginners)
        self.bkt_params = {
            'foundation': {
                'prior': 0.05,      # Start very low
                'transit': 0.4,     # Learn faster at basics
                'slip': 0.1,        # Less mistakes when they know it
                'guess': 0.3        # More guessing allowed
            },
            'building': {
                'prior': 0.08,
                'transit': 0.3,
                'slip': 0.15,
                'guess': 0.25
            },
            'intermediate': {
                'prior': 0.1,
                'transit': 0.25,
                'slip': 0.2,
                'guess': 0.2
            },
            'advanced': {
                'prior': 0.15,
                'transit': 0.2,
                'slip': 0.25,
                'guess': 0.15
            }
        }
        
        # Student tracking
        self.student_states = {}
        self.motivation_levels = {}
        self.recent_performance = {}
        self.learning_streaks = {}
        self.mastery_threshold = mastery_threshold
        
        # Initialize student state with attempts tracking
        self.state = {
            'attempts': {},
            'mastery': {},
            'difficulty_history': {}
        }
        
        # Initialize prerequisite knowledge manager
        self.prerequisite_manager = PrerequisiteManager(mastery_threshold=mastery_threshold * 0.8)
        self.concept_masteries = {}
        
    def get_student_state(self, student_id: str, topic: str) -> StudentState:
        """Determine student state based on recent performance"""
        key = f"{student_id}_{topic}"
        
        if key not in self.student_states:
            return StudentState.LEARNING  # Default state
            
        state = self.student_states[key]
        
        if state['attempts'] < 3:
            return StudentState.LEARNING  # Not enough data
            
        accuracy = state['correct'] / state['attempts'] if state['attempts'] > 0 else 0
        
        if accuracy < 0.3:
            return StudentState.STRUGGLING
        elif accuracy < 0.6:
            return StudentState.LEARNING
        elif accuracy < 0.8:
            return StudentState.PROGRESSING
        else:
            return StudentState.MASTERING
            
    def select_optimal_difficulty(self, student_id: str, topic: str, mastery: float) -> DifficultyLevel:
        """Select optimal difficulty level based on student state and mastery"""
        student_state = self.get_student_state(student_id, topic)
        
        # Check prerequisite readiness
        prerequisite_analysis = self.prerequisite_manager.analyze_concept_readiness(topic)
        prerequisite_factor = 1.0
        
        if not prerequisite_analysis.ready_to_learn:
            # Reduce difficulty if prerequisites aren't mastered
            prerequisite_factor = max(0.6, prerequisite_analysis.overall_readiness)
        
        # Base difficulty selection on student state
        if student_state == StudentState.STRUGGLING:
            # For struggling students, start with foundation level
            if mastery < 0.3:
                return DifficultyLevel.FOUNDATION
            else:
                return DifficultyLevel.BUILDING
                
        elif student_state == StudentState.LEARNING:
            # For learning students, adapt based on mastery
            if mastery < 0.4:
                return DifficultyLevel.FOUNDATION
            else:
                return DifficultyLevel.BUILDING
                
        elif student_state == StudentState.PROGRESSING:
            # For progressing students, challenge appropriately
            if mastery < 0.6:
                return DifficultyLevel.BUILDING
            else:
                return DifficultyLevel.INTERMEDIATE
                
        else:  # MASTERING
            # For mastering students, provide advanced content
            if mastery < 0.8:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.ADVANCED
                
    def should_take_break(self, student_id: str, topic: str) -> bool:
        """Determine if student should take a break based on performance pattern"""
        key = f"{student_id}_{topic}"
        
        if key not in self.recent_performance:
            return False
            
        recent = self.recent_performance[key]
        
        # Check for consistent decline in performance
        if len(recent) >= 5:
            # Check last 5 attempts
            last_five = recent[-5:]
            correct_count = sum(1 for item in last_five if item['correct'])
            
            # If success rate is low and declining, suggest a break
            if correct_count <= 1:
                return True
                
        return False
        
    def provide_motivational_feedback(self, student_id: str, topic: str, is_correct: bool) -> MotivationalFeedback:
        """Provide encouraging, specific feedback with prerequisite suggestions"""
        student_state = self.get_student_state(student_id, topic)
        key = f"{student_id}_{topic}"
        
        # Track learning streaks
        if key not in self.learning_streaks:
            self.learning_streaks[key] = {'correct': 0, 'total': 0}
        
        streak = self.learning_streaks[key]
        if is_correct:
            streak['correct'] += 1
        streak['total'] += 1
        
        # Check for prerequisite gaps
        prerequisite_suggestion = None
        if not is_correct and student_state in [StudentState.STRUGGLING, StudentState.LEARNING]:
            # Check if there are prerequisite gaps
            gaps = self.prerequisite_manager.get_prerequisite_gaps(topic)
            if gaps:
                top_gap = gaps[0]  # Most impactful gap
                prerequisite_suggestion = {
                    "concept_id": top_gap["concept_id"],
                    "concept_name": top_gap["concept_name"],
                    "message": f"You might want to review {top_gap['concept_name']} first to help with this concept."
                }
                next_action = "review_prerequisite"
        
        # Generate contextual feedback
        if student_state == StudentState.STRUGGLING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"🎉 Great job! You're getting it! Keep practicing {topic}",
                    encouragement_level=0.9,
                    next_action="Continue with similar difficulty",
                    prerequisite_suggestion=prerequisite_suggestion
                )
            else:
                return MotivationalFeedback(
                    message=f"💪 Don't worry, {topic} is challenging. Let's try a simpler approach",
                    encouragement_level=0.7,
                    next_action="Provide foundation questions and hints" if not prerequisite_suggestion else "review_prerequisite",
                    prerequisite_suggestion=prerequisite_suggestion
                )
        
        elif student_state == StudentState.LEARNING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"✨ Excellent progress in {topic}! You're building strong foundations",
                    encouragement_level=0.8,
                    next_action="Gradually increase difficulty",
                    prerequisite_suggestion=prerequisite_suggestion
                )
            else:
                return MotivationalFeedback(
                    message=f"🤔 Almost there! Review the concept and try again",
                    encouragement_level=0.6,
                    next_action="Provide worked example" if not prerequisite_suggestion else "review_prerequisite",
                    prerequisite_suggestion=prerequisite_suggestion
                )
        
        elif student_state == StudentState.PROGRESSING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"🚀 Outstanding! You're mastering {topic}",
                    encouragement_level=0.9,
                    next_action="Introduce advanced concepts",
                    prerequisite_suggestion=prerequisite_suggestion
                )
            else:
                return MotivationalFeedback(
                    message=f"📚 Good effort! This was a challenging question",
                    encouragement_level=0.7,
                    next_action="Review specific subtopic" if not prerequisite_suggestion else "review_prerequisite",
                    prerequisite_suggestion=prerequisite_suggestion
                )
        
        else:  # MASTERING
            if is_correct:
                return MotivationalFeedback(
                    message=f"🏆 Perfect! You've mastered {topic}. Ready for new challenges?",
                    encouragement_level=1.0,
                    next_action="Introduce new topic or advanced applications",
                    prerequisite_suggestion=prerequisite_suggestion
                )
            else:
                return MotivationalFeedback(
                    message=f"🎯 Even experts make mistakes! Great learning opportunity",
                    encouragement_level=0.8,
                    next_action="Analyze the error and learn from it" if not prerequisite_suggestion else "review_prerequisite",
                    prerequisite_suggestion=prerequisite_suggestion
                )
                
    def update_mastery(self, student_id: str, topic: str, is_correct: bool, difficulty: float, 
                      response_time_ms: Optional[int] = None, confidence_score: Optional[float] = None) -> Dict[str, Any]:
        """Enhanced BKT update with pedagogical intelligence and prerequisite knowledge integration"""
        key = f"{student_id}_{topic}"
        
        # Get appropriate BKT parameters based on difficulty
        if difficulty < 0.4:
            params = self.bkt_params['foundation']
        elif difficulty < 0.6:
            params = self.bkt_params['building']
        elif difficulty < 0.7:
            params = self.bkt_params['intermediate']
        else:
            params = self.bkt_params['advanced']
        
        # Initialize if first time
        if key not in self.student_states:
            self.student_states[key] = {
                'mastery': params['prior'],
                'attempts': 0,
                'correct': 0,
                'history': []
            }
        
        state = self.student_states[key]
        previous_mastery = state['mastery']
        
        # Standard BKT update
        P_L = previous_mastery
        P_T = params['transit']
        P_S = params['slip']
        P_G = params['guess']
        
        # Evidence probability
        if is_correct:
            P_evidence = P_L * (1 - P_S) + (1 - P_L) * P_G
        else:
            P_evidence = P_L * P_S + (1 - P_L) * (1 - P_G)
        
        # Posterior probability
        if is_correct:
            P_L_given_evidence = (P_L * (1 - P_S)) / max(P_evidence, 0.001)
        else:
            P_L_given_evidence = (P_L * P_S) / max(P_evidence, 0.001)
        
        # Updated mastery with learning
        new_mastery = P_L_given_evidence + (1 - P_L_given_evidence) * P_T
        
        # Pedagogical adjustments
        # 1. Reward consistent correct answers
        if is_correct and key in self.learning_streaks:
            streak = self.learning_streaks[key]
            if streak['correct'] >= 3 and streak['correct'] / max(streak['total'], 1) >= 0.7:
                new_mastery = min(0.95, new_mastery + 0.05)  # Bonus for consistent performance
        
        # 2. Be more forgiving of mistakes for struggling students
        student_state = self.get_student_state(student_id, topic)
        if not is_correct and student_state == StudentState.STRUGGLING:
            # Don't penalize as much for wrong answers when struggling
            new_mastery = max(new_mastery, previous_mastery * 0.9)
        
        # Update state
        if 'attempts' not in state:
            state['attempts'] = 0
            state['correct'] = 0
            
        state['mastery'] = new_mastery
        state['attempts'] += 1
        if is_correct:
            state['correct'] = state.get('correct', 0) + 1
        
        # Track recent performance
        if key not in self.recent_performance:
            self.recent_performance[key] = []
        
        self.recent_performance[key].append({
            'correct': is_correct,
            'difficulty': difficulty,
            'mastery_before': previous_mastery,
            'mastery_after': new_mastery
        })
        
        # Keep only recent attempts
        if len(self.recent_performance[key]) > 20:
            self.recent_performance[key] = self.recent_performance[key][-20:]
        
        # Update concept masteries for prerequisite system
        self.concept_masteries[topic] = new_mastery
        self.prerequisite_manager.sync_mastery_from_bkt(self.concept_masteries)
        
        # Check prerequisite readiness
        prerequisite_analysis = self.prerequisite_manager.analyze_concept_readiness(topic)
        
        # Prepare response with enhanced information
        response = {
            'previous_mastery': previous_mastery,
            'new_mastery': new_mastery,
            'learning_occurred': new_mastery > previous_mastery + 0.01,
            'confidence': min(0.95, new_mastery),
            'attempts': state['attempts'],
            'accuracy': state['correct'] / state['attempts'],
            'student_state': student_state.value,
            'recommended_difficulty': self.select_optimal_difficulty(student_id, topic, new_mastery).value,
            'motivational_feedback': self.provide_motivational_feedback(student_id, topic, is_correct),
            'needs_break': self.should_take_break(student_id, topic)
        }
        
        # Add prerequisite information
        response['prerequisite_readiness'] = {
            'ready_to_learn': prerequisite_analysis.ready_to_learn,
            'overall_readiness': prerequisite_analysis.overall_readiness,
            'gaps_count': len(prerequisite_analysis.prerequisite_gaps),
            'recommended_concepts': prerequisite_analysis.recommended_concepts[:3]  # Top 3 recommendations
        }
        
        return response
        
    def get_learning_path(self, topic: str) -> List[str]:
        """
        Get optimal learning path to reach target concept
        
        Args:
            topic: Target concept to learn
            
        Returns:
            List of concept IDs in recommended learning order
        """
        return self.prerequisite_manager.get_optimal_learning_path(topic)
        
    def recommend_next_concepts(self, current_topic: str, count: int = 3) -> List[str]:
        """
        Recommend next concepts after current concept
        
        Args:
            current_topic: Current concept
            count: Number of recommendations
            
        Returns:
            List of recommended concept IDs
        """
        return self.prerequisite_manager.recommend_next_concepts(current_topic, count)
        
    def load_concept_structure(self, concepts_data: List[Dict]) -> None:
        """
        Load concept structure from database or configuration
        
        Args:
            concepts_data: List of concept dictionaries with structure
        """
        self.prerequisite_manager.load_concept_structure(concepts_data)

class ImprovedSimulation:
    """Test the enhanced BKT system"""
    
    def __init__(self):
        self.enhanced_bkt = PedagogicalBKT()
        
        # Load sample concept structure
        self.load_sample_concepts()
        
    def load_sample_concepts(self):
        """Load sample concept structure for testing"""
        concepts_data = [
            {
                "concept_id": "algebra_basics",
                "name": "Algebra Basics",
                "difficulty": 0.4,
                "prerequisites": []
            },
            {
                "concept_id": "linear_equations",
                "name": "Linear Equations",
                "difficulty": 0.5,
                "prerequisites": [
                    {"concept_id": "algebra_basics", "weight": 0.9}
                ]
            },
            {
                "concept_id": "quadratic_equations",
                "name": "Quadratic Equations",
                "difficulty": 0.7,
                "prerequisites": [
                    {"concept_id": "linear_equations", "weight": 0.8},
                    {"concept_id": "algebra_basics", "weight": 0.6}
                ]
            },
            {
                "concept_id": "polynomials",
                "name": "Polynomials",
                "difficulty": 0.6,
                "prerequisites": [
                    {"concept_id": "algebra_basics", "weight": 0.7}
                ]
            },
            {
                "concept_id": "advanced_functions",
                "name": "Advanced Functions",
                "difficulty": 0.8,
                "prerequisites": [
                    {"concept_id": "quadratic_equations", "weight": 0.8},
                    {"concept_id": "polynomials", "weight": 0.7}
                ]
            }
        ]
        
        self.enhanced_bkt.load_concept_structure(concepts_data)
        
    def simulate_improved_learning(self, days: int = 10):
        """Simulate learning with the enhanced system"""
        print("🚀 Enhanced BKT System - Improved Learning Simulation")
        print("=" * 60)
        
        student_id = "improved_aditya"
        topic = "algebra_basics"
        
        total_correct = 0
        total_questions = 0
        overall_accuracy = 0.0
        
        for day in range(1, days + 1):
            print(f"\n📅 Day {day}")
            daily_correct = 0
            daily_questions = 5
            
            for q in range(daily_questions):
                # Get current mastery
                key = f"{student_id}_{topic}"
                current_mastery = self.enhanced_bkt.student_states.get(key, {}).get('mastery', 0.05)
                
                # Select appropriate difficulty
                difficulty_level = self.enhanced_bkt.select_optimal_difficulty(student_id, topic, current_mastery)
                
                # Convert to numeric difficulty
                difficulty_map = {
                    DifficultyLevel.FOUNDATION: 0.3,
                    DifficultyLevel.BUILDING: 0.5,
                    DifficultyLevel.INTERMEDIATE: 0.65,
                    DifficultyLevel.ADVANCED: 0.8
                }
                difficulty = difficulty_map[difficulty_level]
                
                # Simulate answer (improved success rate based on mastery and difficulty)
                success_probability = min(0.9, max(0.1, current_mastery * (1.2 - difficulty)))
                is_correct = random.random() < success_probability
                
                # Update system
                result = self.enhanced_bkt.update_mastery(student_id, topic, is_correct, difficulty)
                
                if is_correct:
                    daily_correct += 1
                    total_correct += 1
                total_questions += 1
                
                # Show progress
                status = "✅" if is_correct else "❌"
                print(f"    Q{q+1}: {status} (Difficulty: {difficulty_level.value}, Mastery: {result['new_mastery']:.3f})")
                
                # Show motivational feedback
                feedback = result['motivational_feedback']
                print(f"         💬 {feedback.message}")
                
                # Show prerequisite information if available
                if 'prerequisite_readiness' in result:
                    readiness = result['prerequisite_readiness']
                    print(f"         📚 Prerequisite Readiness: {readiness['overall_readiness']:.2f}")
                    if readiness['gaps_count'] > 0:
                        print(f"         🔍 Recommended prerequisites: {', '.join(readiness['recommended_concepts'])}")
                
                # Check for break recommendation
                if result['needs_break']:
                    print(f"         ⏸️ System recommends a break")
                    break
                
                # Check if we should move to next topic based on mastery
                if result['new_mastery'] > 0.85 and day > 3:
                    # Get recommended next concepts
                    next_concepts = self.enhanced_bkt.recommend_next_concepts(topic)
                    if next_concepts:
                        topic = next_concepts[0]
                        print(f"         🆙 Moving to next topic: {topic}")
            
            daily_accuracy = (daily_correct / daily_questions) * 100
            overall_accuracy = (total_correct / total_questions) * 100
            
            print(f"  📊 Day {day}: {daily_correct}/{daily_questions} correct ({daily_accuracy:.1f}%)")
            print(f"  📈 Overall: {total_correct}/{total_questions} correct ({overall_accuracy:.1f}%)")
        
        print(f"\n🎯 Final Results:")
        print(f"   Overall Success Rate: {overall_accuracy:.1f}%")
        print(f"   Total Questions: {total_questions}")
        print(f"   Learning Improvement: {overall_accuracy - 20:.1f}% above baseline")
        
        # Show learning path for advanced topic
        advanced_topic = "advanced_functions"
        learning_path = self.enhanced_bkt.get_learning_path(advanced_topic)
        print(f"\n🛣️ Recommended Learning Path for {advanced_topic}:")
        print(f"   {' → '.join(learning_path)}")
        
        return {
            'success_rate': overall_accuracy,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'improvement': overall_accuracy - 20  # Comparing to baseline
        }

# Example usage
if __name__ == "__main__":
    simulation = ImprovedSimulation()
    results = simulation.simulate_improved_learning(10)
    
    print(f"\n🎉 Enhanced System Performance:")
    print(f"   Success Rate: {results['success_rate']:.1f}%")
    print(f"   Expected Improvement: {results['improvement']:.1f}% over baseline")