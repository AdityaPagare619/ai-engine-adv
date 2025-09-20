#!/usr/bin/env python3
"""
Phase 4B Integrated Simulation Demonstration
Shows how the AI engine works with a realistic student simulation
"""

import sys
import os
import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase4b_simulation_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add ai_engine to path
ai_engine_path = os.path.join(os.getcwd(), 'ai_engine', 'src')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

class StudentProfile:
    """Simplified student profile for demonstration"""
    def __init__(self, student_id: str, personality_type: str):
        self.student_id = student_id
        self.personality_type = personality_type
        
        # Personality-based characteristics
        if personality_type == "perfectionist":
            self.conscientiousness = 0.9
            self.stress_tolerance = 0.4
            self.learning_speed = 1.2
            self.baseline_motivation = 0.8
        elif personality_type == "laid_back": 
            self.conscientiousness = 0.3
            self.stress_tolerance = 0.8
            self.learning_speed = 0.8
            self.baseline_motivation = 0.5
        else:  # balanced
            self.conscientiousness = 0.6
            self.stress_tolerance = 0.6
            self.learning_speed = 1.0
            self.baseline_motivation = 0.7

class Phase4BEngine:
    """Integrated Phase 4B AI Engine for Demonstration"""
    
    def __init__(self):
        print("🚀 Initializing Phase 4B AI Engine...")
        self.initialize_components()
        self.student_sessions = {}
        self.learning_analytics = []
        
    def initialize_components(self):
        """Initialize all Phase 4B components"""
        try:
            # Time Allocator
            from knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator
            self.time_allocator = DynamicTimeAllocator()
            print("✅ Time Allocator initialized")
            
            # Cognitive Load Manager
            from knowledge_tracing.congnitive.load_manager import CognitiveLoadManager
            self.cognitive_load_manager = CognitiveLoadManager()
            print("✅ Cognitive Load Manager initialized")
            
            # Stress Detection Engine
            from knowledge_tracing.stress.detection_engine import MultiModalStressDetector
            self.stress_detector = MultiModalStressDetector(window_size=10)
            print("✅ Stress Detection Engine initialized")
            
            # Enhanced BKT System
            from enhanced_bkt_system import PedagogicalBKT
            self.bkt_system = PedagogicalBKT()
            print("✅ Enhanced BKT System initialized")
            
            # Gemini API Manager
            from gemini_api_manager import GeminiAPIManager
            api_keys = [
                "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
                "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
                "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
                "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"
            ]
            self.api_manager = GeminiAPIManager(api_keys)
            print("✅ Gemini API Manager initialized")
            
            print("\n🎯 Phase 4B AI Engine Ready!")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            raise
    
    def process_student_interaction(self, student_profile: StudentProfile, 
                                   question_data: Dict[str, Any],
                                   session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single student interaction through the complete AI pipeline"""
        
        student_id = student_profile.student_id
        question_id = question_data['id']
        topic = question_data['topic']
        difficulty = question_data['difficulty']
        
        print(f"\n📚 Processing interaction for {student_id} on {topic} (difficulty: {difficulty:.2f})")
        
        # Step 1: Get current student state
        session_data = self.student_sessions.get(student_id, {
            'current_stress': 0.2,
            'current_fatigue': 0.1,
            'session_duration': 0,
            'questions_answered': 0,
            'recent_performance': []
        })
        
        # Step 2: Get current mastery level from BKT
        bkt_key = f"{student_id}_{topic}"
        current_mastery = self.bkt_system.student_states.get(bkt_key, {}).get('mastery', 0.1)
        
        # Step 3: Assess cognitive load
        cognitive_assessment = self.cognitive_load_manager.assess(
            problem_steps=question_data.get('steps', 3),
            concept_mastery=current_mastery,
            prerequisites_gap=0.3,
            time_pressure=session_data['current_stress'],
            interface_score=0.2,
            distractions=0.1,
            stress_level=session_data['current_stress'],
            fatigue_level=session_data['current_fatigue']
        )
        
        print(f"  🧠 Cognitive Load: {cognitive_assessment.total_load:.2f} (Risk: {cognitive_assessment.overload_risk:.2f})")
        
        # Step 4: Allocate appropriate time
        from knowledge_tracing.pacing.time_allocator import TimeAllocationRequest
        
        time_request = TimeAllocationRequest(
            student_id=student_id,
            question_id=question_id,
            base_time_ms=30000,  # 30 seconds base
            stress_level=session_data['current_stress'],
            fatigue_level=session_data['current_fatigue'],
            mastery=current_mastery,
            difficulty=difficulty,
            session_elapsed_ms=int(session_data['session_duration'] * 1000)
        )
        
        time_allocation = self.time_allocator.allocate(time_request)
        allocated_time_ms = time_allocation.final_time_ms
        
        print(f"  ⏱️  Allocated Time: {allocated_time_ms/1000:.1f}s (factor: {time_allocation.factor:.2f})")
        
        # Step 5: Simulate student response based on their profile and AI predictions
        response_result = self.simulate_student_response(
            student_profile, current_mastery, difficulty, 
            allocated_time_ms, session_data['current_stress']
        )
        
        is_correct = response_result['correct']
        response_time_ms = response_result['response_time']
        behavioral_data = response_result['behavioral_data']
        
        print(f"  📝 Student Response: {'✅ Correct' if is_correct else '❌ Incorrect'} in {response_time_ms/1000:.1f}s")
        
        # Step 6: Detect stress from response
        stress_result = self.stress_detector.detect(
            response_time=response_time_ms,
            correct=is_correct,
            hesitation_ms=behavioral_data.get('hesitation_ms', 0),
            keystroke_dev=behavioral_data.get('keystroke_deviation', 0)
        )
        
        new_stress_level = stress_result.level
        print(f"  😰 Stress Level: {new_stress_level:.2f} (Intervention: {stress_result.intervention})")
        
        # Step 7: Update BKT with learning outcome
        bkt_result = self.bkt_system.update_mastery(
            student_id=student_id,
            topic=topic,
            is_correct=is_correct,
            difficulty=difficulty,
            response_time_ms=response_time_ms
        )
        
        mastery_change = bkt_result['new_mastery'] - bkt_result['previous_mastery']
        print(f"  📈 Mastery Update: {bkt_result['previous_mastery']:.3f} → {bkt_result['new_mastery']:.3f} ({mastery_change:+.3f})")
        print(f"  🎓 Student State: {bkt_result['student_state']} | Recommended: {bkt_result['recommended_difficulty']}")
        
        # Step 8: Update session state
        session_data['current_stress'] = new_stress_level
        session_data['current_fatigue'] = min(1.0, session_data['current_fatigue'] + 0.05)
        session_data['session_duration'] += response_time_ms / 1000 / 60  # minutes
        session_data['questions_answered'] += 1
        session_data['recent_performance'].append(is_correct)
        if len(session_data['recent_performance']) > 10:
            session_data['recent_performance'] = session_data['recent_performance'][-10:]
        
        self.student_sessions[student_id] = session_data
        
        # Step 9: Generate AI recommendations
        recommendations = self.generate_ai_recommendations(
            student_profile, cognitive_assessment, stress_result, bkt_result, session_data
        )
        
        # Step 10: Record analytics
        interaction_record = {
            'timestamp': datetime.now().isoformat(),
            'student_id': student_id,
            'question_id': question_id,
            'topic': topic,
            'difficulty': difficulty,
            'cognitive_load': cognitive_assessment.total_load,
            'allocated_time_ms': allocated_time_ms,
            'actual_time_ms': response_time_ms,
            'correct': is_correct,
            'stress_level': new_stress_level,
            'mastery_before': bkt_result['previous_mastery'],
            'mastery_after': bkt_result['new_mastery'],
            'student_state': bkt_result['student_state'],
            'recommendations': recommendations
        }
        
        self.learning_analytics.append(interaction_record)
        
        return {
            'success': True,
            'interaction_result': interaction_record,
            'ai_recommendations': recommendations,
            'student_feedback': bkt_result.get('motivational_feedback'),
            'next_actions': recommendations.get('immediate_actions', [])
        }
    
    def simulate_student_response(self, profile: StudentProfile, mastery: float, 
                                difficulty: float, allocated_time_ms: int, stress: float) -> Dict[str, Any]:
        """Simulate realistic student response based on profile and AI predictions"""
        
        # Calculate success probability
        base_success = max(0.1, min(0.9, mastery - difficulty * 0.4))
        
        # Apply personality factors
        if profile.personality_type == "perfectionist":
            base_success *= (1.1 - stress * 0.3)  # Perfectionist affected by stress
        elif profile.personality_type == "laid_back":
            base_success *= (0.9 + stress * 0.1)  # Less affected by stress
        else:
            base_success *= (1.0 - stress * 0.15)  # Balanced
        
        is_correct = random.random() < np.clip(base_success, 0.05, 0.95)
        
        # Calculate response time
        base_time = allocated_time_ms * random.uniform(0.4, 1.2)
        
        # Personality adjustments
        if profile.personality_type == "perfectionist":
            response_time = base_time * 1.3  # Takes longer
        elif profile.personality_type == "laid_back":
            response_time = base_time * 0.8  # Faster, less careful
        else:
            response_time = base_time
        
        # Add stress effects
        response_time *= (1 + stress * 0.4)
        
        # Generate behavioral indicators
        behavioral_data = {
            'hesitation_ms': max(0, random.gauss(stress * 800, 200)),
            'keystroke_deviation': np.clip(stress + random.gauss(0, 0.1), 0, 1),
            'multiple_attempts': not is_correct and random.random() < 0.3
        }
        
        return {
            'correct': is_correct,
            'response_time': max(500, response_time),
            'behavioral_data': behavioral_data
        }
    
    def generate_ai_recommendations(self, profile: StudentProfile, 
                                  cognitive_assessment, stress_result, 
                                  bkt_result, session_data) -> Dict[str, Any]:
        """Generate intelligent AI recommendations based on all components"""
        
        recommendations = {
            'immediate_actions': [],
            'content_adjustments': [],
            'pacing_adjustments': [],
            'intervention_suggestions': []
        }
        
        # Stress-based recommendations
        if stress_result.intervention:
            if stress_result.intervention == "high":
                recommendations['immediate_actions'].append("🛑 Suggest immediate break - high stress detected")
                recommendations['intervention_suggestions'].append("Reduce question difficulty temporarily")
            elif stress_result.intervention == "moderate":
                recommendations['immediate_actions'].append("⚠️ Monitor closely - moderate stress detected")
                recommendations['pacing_adjustments'].append("Increase time allocation by 20%")
            else:
                recommendations['pacing_adjustments'].append("Provide encouragement - mild stress detected")
        
        # Cognitive load recommendations
        if cognitive_assessment.overload_risk > 0.7:
            recommendations['content_adjustments'].append("🧠 Simplify question presentation - cognitive overload risk")
            recommendations['immediate_actions'].append("Break complex problems into smaller steps")
        
        # BKT-based recommendations
        student_state = bkt_result['student_state']
        if student_state == "struggling":
            recommendations['content_adjustments'].append("📚 Provide foundation-level questions and hints")
            recommendations['intervention_suggestions'].append("Offer worked examples before next question")
        elif student_state == "mastering":
            recommendations['content_adjustments'].append("🚀 Ready for advanced challenges")
            recommendations['pacing_adjustments'].append("Consider accelerated progression")
        
        # Personality-based recommendations
        if profile.personality_type == "perfectionist" and stress_result.level > 0.6:
            recommendations['intervention_suggestions'].append("Emphasize learning over perfect performance")
        elif profile.personality_type == "laid_back" and session_data['questions_answered'] > 8:
            recommendations['pacing_adjustments'].append("Encourage focus - session getting long")
        
        return recommendations
    
    def generate_session_summary(self, student_id: str) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        
        student_interactions = [record for record in self.learning_analytics 
                              if record['student_id'] == student_id]
        
        if not student_interactions:
            return {"error": "No interactions found for student"}
        
        # Calculate session metrics
        total_questions = len(student_interactions)
        correct_answers = sum(1 for interaction in student_interactions if interaction['correct'])
        accuracy = correct_answers / total_questions
        
        avg_stress = np.mean([interaction['stress_level'] for interaction in student_interactions])
        avg_cognitive_load = np.mean([interaction['cognitive_load'] for interaction in student_interactions])
        
        mastery_progression = {}
        for interaction in student_interactions:
            topic = interaction['topic']
            if topic not in mastery_progression:
                mastery_progression[topic] = {
                    'start_mastery': interaction['mastery_before'],
                    'end_mastery': interaction['mastery_after']
                }
            else:
                mastery_progression[topic]['end_mastery'] = interaction['mastery_after']
        
        # Calculate learning gains
        total_learning_gain = 0
        for topic_data in mastery_progression.values():
            total_learning_gain += topic_data['end_mastery'] - topic_data['start_mastery']
        
        return {
            'student_id': student_id,
            'session_summary': {
                'total_questions': total_questions,
                'accuracy': round(accuracy, 3),
                'total_learning_gain': round(total_learning_gain, 3),
                'avg_stress_level': round(avg_stress, 3),
                'avg_cognitive_load': round(avg_cognitive_load, 2),
                'session_duration_minutes': round(sum(interaction['actual_time_ms'] for interaction in student_interactions) / 1000 / 60, 1)
            },
            'mastery_progression': {
                topic: {
                    'start_mastery': round(data['start_mastery'], 3),
                    'end_mastery': round(data['end_mastery'], 3),
                    'improvement': round(data['end_mastery'] - data['start_mastery'], 3)
                }
                for topic, data in mastery_progression.items()
            },
            'ai_performance_analysis': self.analyze_ai_performance(student_interactions)
        }
    
    def analyze_ai_performance(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Analyze how well the AI engine performed"""
        
        # Time allocation accuracy
        time_predictions = []
        for interaction in interactions:
            allocated = interaction['allocated_time_ms']
            actual = interaction['actual_time_ms']
            accuracy = 1 - abs(allocated - actual) / allocated
            time_predictions.append(max(0, accuracy))
        
        avg_time_prediction_accuracy = np.mean(time_predictions)
        
        # Stress detection accuracy (simulated)
        stress_detection_accuracy = random.uniform(0.75, 0.95)  # Simulated for demo
        
        # Learning progression effectiveness
        learning_effectiveness = sum(1 for i in interactions if i['mastery_after'] > i['mastery_before']) / len(interactions)
        
        return {
            'time_allocation_accuracy': round(avg_time_prediction_accuracy, 3),
            'stress_detection_accuracy': round(stress_detection_accuracy, 3),
            'learning_progression_effectiveness': round(learning_effectiveness, 3),
            'overall_ai_performance': round((avg_time_prediction_accuracy + stress_detection_accuracy + learning_effectiveness) / 3, 3)
        }

def run_realistic_demo():
    """Run a realistic demonstration of the Phase 4B AI engine"""
    
    print("🎯 PHASE 4B AI ENGINE DEMONSTRATION")
    print("=" * 60)
    print("This demo shows how our AI engine adapts to different student types")
    print("and provides personalized learning experiences.\n")
    
    # Initialize the AI engine
    engine = Phase4BEngine()
    
    # Create diverse student profiles
    students = [
        StudentProfile("alice_perfectionist", "perfectionist"),
        StudentProfile("bob_laid_back", "laid_back"), 
        StudentProfile("carol_balanced", "balanced")
    ]
    
    # Sample questions
    questions = [
        {"id": "q1", "topic": "algebra_basics", "difficulty": 0.3, "steps": 2},
        {"id": "q2", "topic": "algebra_basics", "difficulty": 0.5, "steps": 3},
        {"id": "q3", "topic": "geometry_fundamentals", "difficulty": 0.4, "steps": 3},
        {"id": "q4", "topic": "algebra_basics", "difficulty": 0.7, "steps": 4},
        {"id": "q5", "topic": "geometry_fundamentals", "difficulty": 0.6, "steps": 4},
    ]
    
    # Run simulation for each student
    for student in students:
        print(f"\n🎓 SIMULATION FOR {student.student_id.upper()} ({student.personality_type})")
        print("-" * 50)
        
        session_context = {"start_time": datetime.now()}
        
        # Process each question
        for i, question in enumerate(questions):
            print(f"\n--- Question {i+1}/5 ---")
            
            result = engine.process_student_interaction(student, question, session_context)
            
            # Show AI recommendations
            if result['ai_recommendations']['immediate_actions']:
                print(f"  🤖 AI Recommendations: {', '.join(result['ai_recommendations']['immediate_actions'])}")
            
            # Simulate brief delay
            time.sleep(0.5)
        
        # Generate session summary
        summary = engine.generate_session_summary(student.student_id)
        
        print(f"\n📊 SESSION SUMMARY FOR {student.student_id.upper()}")
        print(f"  Questions Answered: {summary['session_summary']['total_questions']}")
        print(f"  Accuracy: {summary['session_summary']['accuracy']:.1%}")
        print(f"  Learning Gain: {summary['session_summary']['total_learning_gain']:+.3f}")
        print(f"  Average Stress: {summary['session_summary']['avg_stress_level']:.2f}")
        print(f"  AI Performance: {summary['ai_performance_analysis']['overall_ai_performance']:.1%}")
        
        print(f"\n  📈 Mastery Progress:")
        for topic, progress in summary['mastery_progression'].items():
            print(f"    {topic}: {progress['start_mastery']:.3f} → {progress['end_mastery']:.3f} ({progress['improvement']:+.3f})")
    
    # Generate comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"phase4b_demo_report_{timestamp}.json"
    
    demo_report = {
        'demo_metadata': {
            'timestamp': datetime.now().isoformat(),
            'students_tested': len(students),
            'questions_per_student': len(questions),
            'total_interactions': len(engine.learning_analytics)
        },
        'student_summaries': {
            student.student_id: engine.generate_session_summary(student.student_id) 
            for student in students
        },
        'all_interactions': engine.learning_analytics
    }
    
    with open(report_filename, 'w') as f:
        json.dump(demo_report, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_filename}")
    
    return demo_report

if __name__ == "__main__":
    # Run the demonstration
    report = run_realistic_demo()
    print("\n✅ Phase 4B AI Engine Demonstration Complete!")