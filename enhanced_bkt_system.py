#!/usr/bin/env python3
"""
Enhanced BKT System with Pedagogical Intelligence
Addresses the 5.3% success rate issue with smart teaching methods
"""

import random
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

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

class PedagogicalBKT:
    """Enhanced BKT with teaching intelligence"""
    
    def __init__(self):
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
        
    def get_student_state(self, student_id: str, topic: str) -> StudentState:
        """Determine current student emotional/learning state"""
        key = f"{student_id}_{topic}"
        recent_accuracy = self.get_recent_accuracy(student_id, topic)
        
        if recent_accuracy < 0.3:
            return StudentState.STRUGGLING
        elif recent_accuracy < 0.6:
            return StudentState.LEARNING
        elif recent_accuracy < 0.8:
            return StudentState.PROGRESSING
        else:
            return StudentState.MASTERING
    
    def get_recent_accuracy(self, student_id: str, topic: str) -> float:
        """Get accuracy from last 5-10 questions"""
        key = f"{student_id}_{topic}"
        if key not in self.recent_performance:
            return 0.5  # Neutral starting point
        
        recent_attempts = self.recent_performance[key][-10:]  # Last 10 attempts
        if not recent_attempts:
            return 0.5
        
        correct_count = sum(1 for attempt in recent_attempts if attempt['correct'])
        return correct_count / len(recent_attempts)
    
    def select_optimal_difficulty(self, student_id: str, topic: str, current_mastery: float) -> DifficultyLevel:
        """Smart difficulty selection based on student state"""
        student_state = self.get_student_state(student_id, topic)
        recent_accuracy = self.get_recent_accuracy(student_id, topic)
        
        # STRUGGLING students need easier questions
        if student_state == StudentState.STRUGGLING:
            return DifficultyLevel.FOUNDATION
        
        # LEARNING students need careful progression
        elif student_state == StudentState.LEARNING:
            if recent_accuracy > 0.4:
                return DifficultyLevel.BUILDING
            else:
                return DifficultyLevel.FOUNDATION
        
        # PROGRESSING students can handle medium challenges
        elif student_state == StudentState.PROGRESSING:
            if current_mastery > 0.6:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.BUILDING
        
        # MASTERING students need advanced challenges
        else:
            return DifficultyLevel.ADVANCED
    
    def provide_motivational_feedback(self, student_id: str, topic: str, is_correct: bool) -> MotivationalFeedback:
        """Provide encouraging, specific feedback"""
        student_state = self.get_student_state(student_id, topic)
        key = f"{student_id}_{topic}"
        
        # Track learning streaks
        if key not in self.learning_streaks:
            self.learning_streaks[key] = {'correct': 0, 'total': 0}
        
        streak = self.learning_streaks[key]
        if is_correct:
            streak['correct'] += 1
        streak['total'] += 1
        
        # Generate contextual feedback
        if student_state == StudentState.STRUGGLING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"🎉 Great job! You're getting it! Keep practicing {topic}",
                    encouragement_level=0.9,
                    next_action="Continue with similar difficulty"
                )
            else:
                return MotivationalFeedback(
                    message=f"💪 Don't worry, {topic} is challenging. Let's try a simpler approach",
                    encouragement_level=0.7,
                    next_action="Provide foundation questions and hints"
                )
        
        elif student_state == StudentState.LEARNING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"✨ Excellent progress in {topic}! You're building strong foundations",
                    encouragement_level=0.8,
                    next_action="Gradually increase difficulty"
                )
            else:
                return MotivationalFeedback(
                    message=f"🤔 Almost there! Review the concept and try again",
                    encouragement_level=0.6,
                    next_action="Provide worked example"
                )
        
        elif student_state == StudentState.PROGRESSING:
            if is_correct:
                return MotivationalFeedback(
                    message=f"🚀 Outstanding! You're mastering {topic}",
                    encouragement_level=0.9,
                    next_action="Introduce advanced concepts"
                )
            else:
                return MotivationalFeedback(
                    message=f"📚 Good effort! This was a challenging question",
                    encouragement_level=0.7,
                    next_action="Review specific subtopic"
                )
        
        else:  # MASTERING
            if is_correct:
                return MotivationalFeedback(
                    message=f"🏆 Perfect! You've mastered {topic}. Ready for new challenges?",
                    encouragement_level=1.0,
                    next_action="Introduce new topic or advanced applications"
                )
            else:
                return MotivationalFeedback(
                    message=f"🎯 Even experts make mistakes! Great learning opportunity",
                    encouragement_level=0.8,
                    next_action="Analyze the error and learn from it"
                )
    
    def should_take_break(self, student_id: str, topic: str) -> bool:
        """Detect when student needs a break"""
        key = f"{student_id}_{topic}"
        if key not in self.recent_performance:
            return False
        
        recent_attempts = self.recent_performance[key][-5:]  # Last 5 attempts
        if len(recent_attempts) < 5:
            return False
        
        # Check for consecutive failures
        consecutive_wrong = sum(1 for attempt in recent_attempts[-3:] if not attempt['correct'])
        if consecutive_wrong >= 3:
            return True
        
        # Check for declining performance
        first_half_accuracy = sum(1 for attempt in recent_attempts[:3] if attempt['correct']) / 3
        second_half_accuracy = sum(1 for attempt in recent_attempts[3:] if attempt['correct']) / 2
        
        if first_half_accuracy - second_half_accuracy > 0.5:  # Performance dropped significantly
            return True
        
        return False
    
    def update_mastery(self, student_id: str, topic: str, is_correct: bool, difficulty: float, 
                      response_time_ms: Optional[int] = None, confidence_score: Optional[float] = None) -> Dict[str, Any]:
        """Enhanced BKT update with pedagogical intelligence"""
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
        state['mastery'] = new_mastery
        state['attempts'] += 1
        if is_correct:
            state['correct'] += 1
        
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
        
        return {
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

class ImprovedSimulation:
    """Test the enhanced BKT system"""
    
    def __init__(self):
        self.enhanced_bkt = PedagogicalBKT()
        
    def simulate_improved_learning(self, days: int = 10):
        """Simulate learning with the enhanced system"""
        print("🚀 Enhanced BKT System - Improved Learning Simulation")
        print("=" * 60)
        
        student_id = "improved_aditya"
        topic = "algebra_basics"
        
        total_correct = 0
        total_questions = 0
        
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
                
                # Check for break recommendation
                if result['needs_break']:
                    print(f"         ⏸️ System recommends a break")
                    break
            
            daily_accuracy = (daily_correct / daily_questions) * 100
            overall_accuracy = (total_correct / total_questions) * 100
            
            print(f"  📊 Day {day}: {daily_correct}/{daily_questions} correct ({daily_accuracy:.1f}%)")
            print(f"  📈 Overall: {total_correct}/{total_questions} correct ({overall_accuracy:.1f}%)")
        
        print(f"\n🎯 Final Results:")
        print(f"   Overall Success Rate: {overall_accuracy:.1f}%")
        print(f"   Total Questions: {total_questions}")
        print(f"   Learning Improvement: {overall_accuracy - 20:.1f}% above baseline")
        
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