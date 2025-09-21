#!/usr/bin/env python3
"""
One Month Simulation for AI Engine Testing
Simulates 3 students taking 3 different exam types over a 1-month period
Tests integration between BKT and Phase 4B components
"""

import os
import sys
import json
import random
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required components
from enhanced_bkt_system import PedagogicalBKT
from gemini_api_manager import GeminiAPIManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simulation_log.txt')
    ]
)
logger = logging.getLogger(__name__)

# Define student profiles
@dataclass
class StudentProfile:
    """Student profile with learning characteristics"""
    student_id: str
    name: str
    personality_type: str
    learning_style: str
    strengths: List[str]
    weaknesses: List[str]
    initial_mastery: Dict[str, float]
    stress_tolerance: float  # 0.0 to 1.0
    motivation: float  # 0.0 to 1.0

# Define exam types
class ExamType(Enum):
    JEE_MAINS = "JEE_Mains"
    NEET = "NEET"
    JEE_ADVANCED = "JEE_Advanced"

# Define simulation calendar
@dataclass
class SimulationEvent:
    """An event in the simulation calendar"""
    day: int
    student_id: str
    exam_type: ExamType
    topics: List[str]
    question_count: int
    difficulty_range: tuple
    time_pressure: float  # 0.0 to 1.0
    importance: float  # 0.0 to 1.0

class OneMonthSimulation:
    """Simulates 3 students taking 3 exam types over 1 month"""
    
    def __init__(self):
        """Initialize the simulation"""
        logger.info("🚀 Initializing One Month Simulation...")
        
        # Initialize components
        self.bkt_system = PedagogicalBKT()
        
        # API keys for Gemini
        api_keys = [
            "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
            "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
            "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
            "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"
        ]
        self.api_manager = GeminiAPIManager(api_keys)
        
        # Create student profiles
        self.students = self.create_student_profiles()
        
        # Create simulation calendar
        self.calendar = self.create_simulation_calendar()
        
        # Results tracking
        self.results = {
            "students": {},
            "exams": {},
            "daily_stats": {},
            "mastery_progression": {},
            "system_performance": {
                "api_calls": 0,
                "processing_times": []
            }
        }
        
        logger.info("✅ Simulation initialized with 3 students and 1-month calendar")
    
    def create_student_profiles(self) -> Dict[str, StudentProfile]:
        """Create diverse student profiles"""
        students = {
            "student_1": StudentProfile(
                student_id="student_1",
                name="Raj Kumar",
                personality_type="perfectionist",
                learning_style="visual",
                strengths=["Physics", "Mathematics"],
                weaknesses=["Chemistry", "Biology"],
                initial_mastery={
                    "mechanics": 0.6,
                    "electromagnetism": 0.4,
                    "thermodynamics": 0.3,
                    "organic_chemistry": 0.2,
                    "inorganic_chemistry": 0.3,
                    "algebra": 0.7,
                    "calculus": 0.6
                },
                stress_tolerance=0.6,
                motivation=0.8
            ),
            "student_2": StudentProfile(
                student_id="student_2",
                name="Priya Singh",
                personality_type="balanced",
                learning_style="auditory",
                strengths=["Chemistry", "Biology"],
                weaknesses=["Physics", "Calculus"],
                initial_mastery={
                    "mechanics": 0.3,
                    "electromagnetism": 0.2,
                    "thermodynamics": 0.4,
                    "organic_chemistry": 0.7,
                    "inorganic_chemistry": 0.6,
                    "algebra": 0.5,
                    "calculus": 0.3
                },
                stress_tolerance=0.7,
                motivation=0.7
            ),
            "student_3": StudentProfile(
                student_id="student_3",
                name="Arjun Patel",
                personality_type="laid_back",
                learning_style="kinesthetic",
                strengths=["Problem Solving", "Algebra"],
                weaknesses=["Memorization", "Time Management"],
                initial_mastery={
                    "mechanics": 0.5,
                    "electromagnetism": 0.5,
                    "thermodynamics": 0.4,
                    "organic_chemistry": 0.3,
                    "inorganic_chemistry": 0.4,
                    "algebra": 0.6,
                    "calculus": 0.5
                },
                stress_tolerance=0.8,
                motivation=0.6
            )
        }
        
        # Initialize BKT states for each student and topic
        for student_id, profile in students.items():
            for topic, mastery in profile.initial_mastery.items():
                self.bkt_system.student_states[f"{student_id}_{topic}"] = {
                    "mastery": mastery,
                    "practice_count": int(mastery * 10)  # Simulate prior practice
                }
        
        return students
    
    def create_simulation_calendar(self) -> List[SimulationEvent]:
        """Create a 30-day simulation calendar with study events"""
        calendar = []
        
        # Define topics for each exam type
        exam_topics = {
            ExamType.JEE_MAINS: ["mechanics", "electromagnetism", "algebra", "calculus"],
            ExamType.NEET: ["organic_chemistry", "inorganic_chemistry", "biology", "physics_basics"],
            ExamType.JEE_ADVANCED: ["advanced_mechanics", "thermodynamics", "advanced_calculus", "modern_physics"]
        }
        
        # Create events for each student
        for student_id in self.students.keys():
            # Each student takes each exam type multiple times over the month
            for day in range(1, 31):
                # Determine if there's an exam today (2-3 days between exams)
                if day % 3 == 0:
                    # Rotate through exam types
                    exam_index = (day // 3) % 3
                    exam_type = list(ExamType)[exam_index]
                    
                    # Select topics for this exam (2-3 topics per exam)
                    available_topics = exam_topics[exam_type]
                    topics = random.sample(available_topics, min(3, len(available_topics)))
                    
                    # Create the event
                    calendar.append(SimulationEvent(
                        day=day,
                        student_id=student_id,
                        exam_type=exam_type,
                        topics=topics,
                        question_count=random.randint(5, 10),
                        difficulty_range=(0.3, 0.8),
                        time_pressure=random.uniform(0.2, 0.8),
                        importance=random.uniform(0.4, 0.9)
                    ))
        
        return calendar
    
    def simulate_question_response(self, student: StudentProfile, topic: str, 
                                  difficulty: float, time_pressure: float) -> Dict[str, Any]:
        """Simulate a student's response to a question"""
        # Get current mastery from BKT
        mastery = self.bkt_system.student_states.get(f"{student.student_id}_{topic}", {"mastery": 0.1})["mastery"]
        
        # Calculate success probability based on mastery and difficulty
        base_probability = max(0.1, min(0.9, mastery - (difficulty * 0.5)))
        
        # Apply personality and stress factors
        if student.personality_type == "perfectionist":
            # Perfectionists do better with less time pressure
            success_probability = base_probability * (1.0 - (time_pressure * 0.3))
        elif student.personality_type == "laid_back":
            # Laid back students are less affected by time pressure
            success_probability = base_probability * (1.0 - (time_pressure * 0.1))
        else:
            # Balanced students
            success_probability = base_probability * (1.0 - (time_pressure * 0.2))
        
        # Determine if correct
        is_correct = random.random() < success_probability
        
        # Calculate response time (in milliseconds)
        base_time = 30000  # 30 seconds base time
        
        # Adjust for difficulty
        time_factor = 1.0 + (difficulty * 1.5)
        
        # Adjust for personality
        if student.personality_type == "perfectionist":
            time_factor *= 1.2  # Takes longer
        elif student.personality_type == "laid_back":
            time_factor *= 0.8  # Takes less time
        
        # Adjust for mastery
        time_factor *= (1.0 - (mastery * 0.3))
        
        # Calculate final time
        response_time_ms = int(base_time * time_factor)
        
        # Simulate behavioral data
        hesitation_ms = int(response_time_ms * 0.2) if not is_correct else int(response_time_ms * 0.1)
        keystroke_deviation = random.uniform(0.2, 0.6) if not is_correct else random.uniform(0.1, 0.3)
        
        return {
            "is_correct": is_correct,
            "response_time_ms": response_time_ms,
            "behavioral_data": {
                "hesitation_ms": hesitation_ms,
                "keystroke_deviation": keystroke_deviation
            }
        }
    
    def run_simulation(self):
        """Run the full one-month simulation"""
        logger.info("🏁 Starting One Month Simulation...")
        
        # Process each day in the simulation
        for day in range(1, 31):
            logger.info(f"📅 Simulation Day {day}")
            
            # Get events for today
            today_events = [event for event in self.calendar if event.day == day]
            
            # Process each event
            for event in today_events:
                student = self.students[event.student_id]
                logger.info(f"  👨‍🎓 {student.name} taking {event.exam_type.value} exam")
                
                # Track results for this exam
                exam_results = {
                    "student_id": student.student_id,
                    "exam_type": event.exam_type.value,
                    "day": day,
                    "topics": event.topics,
                    "questions": [],
                    "correct_count": 0,
                    "total_time_ms": 0
                }
                
                # Process each question in the exam
                for q in range(event.question_count):
                    # Select topic and difficulty
                    topic = random.choice(event.topics)
                    difficulty = random.uniform(event.difficulty_range[0], event.difficulty_range[1])
                    
                    # Simulate response
                    start_time = time.time()
                    response = self.simulate_question_response(
                        student=student,
                        topic=topic,
                        difficulty=difficulty,
                        time_pressure=event.time_pressure
                    )
                    processing_time = time.time() - start_time
                    
                    # Update BKT with the result
                    bkt_result = self.bkt_system.update_mastery(
                        student_id=student.student_id,
                        topic=topic,
                        is_correct=response["is_correct"],
                        difficulty=difficulty,
                        response_time_ms=response["response_time_ms"]
                    )
                    
                    # Track question result
                    question_result = {
                        "topic": topic,
                        "difficulty": difficulty,
                        "is_correct": response["is_correct"],
                        "response_time_ms": response["response_time_ms"],
                        "previous_mastery": bkt_result["previous_mastery"],
                        "new_mastery": bkt_result["new_mastery"],
                        "mastery_change": bkt_result["new_mastery"] - bkt_result["previous_mastery"]
                    }
                    
                    exam_results["questions"].append(question_result)
                    
                    if response["is_correct"]:
                        exam_results["correct_count"] += 1
                    
                    exam_results["total_time_ms"] += response["response_time_ms"]
                    
                    # Log question result
                    status = "✅" if response["is_correct"] else "❌"
                    logger.info(f"    Q{q+1} ({topic}): {status} - Mastery: {bkt_result['previous_mastery']:.2f} → {bkt_result['new_mastery']:.2f}")
                
                # Calculate exam statistics
                exam_results["accuracy"] = exam_results["correct_count"] / event.question_count
                exam_results["avg_time_per_question"] = exam_results["total_time_ms"] / event.question_count
                
                # Store exam results
                exam_id = f"{student.student_id}_{event.exam_type.value}_{day}"
                self.results["exams"][exam_id] = exam_results
                
                # Log exam summary
                logger.info(f"    📊 Result: {exam_results['correct_count']}/{event.question_count} correct ({exam_results['accuracy']:.1%})")
            
            # Track daily mastery progression for each student and topic
            for student_id, student in self.students.items():
                if student_id not in self.results["mastery_progression"]:
                    self.results["mastery_progression"][student_id] = {}
                
                for topic in set(topic for event in self.calendar for topic in event.topics):
                    key = f"{student_id}_{topic}"
                    if key in self.bkt_system.student_states:
                        mastery = self.bkt_system.student_states[key]["mastery"]
                        
                        if topic not in self.results["mastery_progression"][student_id]:
                            self.results["mastery_progression"][student_id][topic] = []
                        
                        self.results["mastery_progression"][student_id][topic].append({
                            "day": day,
                            "mastery": mastery
                        })
        
        logger.info("✅ One Month Simulation completed successfully")
        return self.results
    
    def save_results(self, filename=None):
        """Save simulation results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📋 Simulation results saved to {filename}")
        return filename
    
    def generate_report(self):
        """Generate a summary report of the simulation"""
        report = {
            "simulation_period": "30 days",
            "students": len(self.students),
            "total_exams": len(self.results["exams"]),
            "student_performance": {},
            "topic_difficulty": {},
            "mastery_growth": {},
            "system_performance": {
                "avg_processing_time": sum(self.results["system_performance"]["processing_times"]) / 
                                      len(self.results["system_performance"]["processing_times"])
                                      if self.results["system_performance"]["processing_times"] else 0,
                "total_api_calls": self.results["system_performance"]["api_calls"]
            }
        }
        
        # Calculate student performance
        for student_id, student in self.students.items():
            student_exams = [exam for exam_id, exam in self.results["exams"].items() 
                            if exam["student_id"] == student_id]
            
            if student_exams:
                avg_accuracy = sum(exam["accuracy"] for exam in student_exams) / len(student_exams)
                
                report["student_performance"][student_id] = {
                    "name": student.name,
                    "exams_taken": len(student_exams),
                    "avg_accuracy": avg_accuracy,
                    "personality_type": student.personality_type
                }
        
        # Calculate mastery growth
        for student_id, topics in self.results["mastery_progression"].items():
            report["mastery_growth"][student_id] = {}
            
            for topic, progression in topics.items():
                if progression:
                    initial = progression[0]["mastery"] if progression else 0
                    final = progression[-1]["mastery"] if progression else 0
                    growth = final - initial
                    
                    report["mastery_growth"][student_id][topic] = {
                        "initial": initial,
                        "final": final,
                        "growth": growth
                    }
        
        return report

def main():
    """Run the one-month simulation"""
    # Create and run simulation
    simulation = OneMonthSimulation()
    results = simulation.run_simulation()
    
    # Save results
    simulation.save_results()
    
    # Generate and print report
    report = simulation.generate_report()
    print("\n" + "=" * 60)
    print("📊 SIMULATION SUMMARY REPORT")
    print("=" * 60)
    print(f"Period: {report['simulation_period']}")
    print(f"Students: {report['students']}")
    print(f"Total Exams: {report['total_exams']}")
    
    print("\n👨‍🎓 STUDENT PERFORMANCE:")
    for student_id, performance in report["student_performance"].items():
        print(f"  {performance['name']} ({performance['personality_type']}): {performance['avg_accuracy']:.1%} accuracy across {performance['exams_taken']} exams")
    
    print("\n📈 MASTERY GROWTH:")
    for student_id, topics in report["mastery_growth"].items():
        student_name = simulation.students[student_id].name
        print(f"  {student_name}:")
        for topic, growth in topics.items():
            print(f"    {topic}: {growth['initial']:.2f} → {growth['final']:.2f} ({growth['growth']:+.2f})")
    
    print("\n✅ Simulation complete!")

if __name__ == "__main__":
    main()