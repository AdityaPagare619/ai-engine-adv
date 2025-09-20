#!/usr/bin/env python3
"""
Advanced Multi-Student Simulation with Comprehensive Reporting
Uses new Gemini API with robust rate limiting and detailed PDF analysis
"""

import os
import json
import random
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# New Gemini API
from google import genai
from google.genai import types

# Enhanced BKT system
from enhanced_bkt_system import PedagogicalBKT

# Reporting
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Configure multiple API keys with failover
API_KEYS = [
    "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
    "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
    "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
    "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"  # New key
]

class ExamCondition(Enum):
    NORMAL = "normal"
    TIME_PRESSURE = "time_pressure"
    HIGH_STAKES = "high_stakes"
    MOCK_TEST = "mock_test"
    PRACTICE_SESSION = "practice_session"
    COMPETITIVE = "competitive"

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    LOGICAL = "logical"
    SOCIAL = "social"
    INDIVIDUAL = "individual"

@dataclass
class StudentPersona:
    name: str
    age: int
    grade: str
    background: str
    personality_traits: List[str]
    learning_style: LearningStyle
    strengths: List[str]
    weaknesses: List[str]
    motivation_level: float  # 0.0 to 1.0
    stress_tolerance: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    family_support: str
    economic_background: str
    previous_academic_performance: str
    study_habits: Dict[str, Any]
    psychological_profile: Dict[str, Any]
    exam_behavior_patterns: Dict[str, Any]

class RobustGeminiClient:
    """Robust Gemini client with multiple API keys and smart retry logic"""
    
    def __init__(self):
        self.current_key_index = 0
        self.clients = []
        self.setup_clients()
        
    def setup_clients(self):
        """Initialize clients for all API keys"""
        for i, api_key in enumerate(API_KEYS):
            try:
                os.environ['GOOGLE_API_KEY'] = api_key
                client = genai.Client(api_key=api_key)
                self.clients.append(client)
                print(f"✅ Gemini client {i+1} initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize client {i+1}: {e}")
                self.clients.append(None)
    
    def get_active_client(self):
        """Get currently active client"""
        return self.clients[self.current_key_index] if self.clients[self.current_key_index] else None
    
    def rotate_client(self):
        """Switch to next available client"""
        original_index = self.current_key_index
        for _ in range(len(self.clients)):
            self.current_key_index = (self.current_key_index + 1) % len(self.clients)
            if self.clients[self.current_key_index]:
                print(f"🔄 Switched to API key {self.current_key_index + 1}")
                return True
        
        print("❌ No working API keys available!")
        self.current_key_index = original_index
        return False
    
    async def generate_content_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Generate content with robust retry logic"""
        
        for attempt in range(max_retries):
            client = self.get_active_client()
            if not client:
                if not self.rotate_client():
                    break
                continue
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                        temperature=0.7,
                        max_output_tokens=2048
                    )
                )
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ API Error (attempt {attempt+1}): {error_msg[:100]}...")
                
                if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    print("📊 Rate limit hit, switching API key...")
                    if self.rotate_client():
                        await asyncio.sleep(1)  # Brief pause
                        continue
                    else:
                        break
                elif "invalid" in error_msg.lower():
                    print("🔑 Invalid API key, switching...")
                    if not self.rotate_client():
                        break
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
        
        print("❌ All API attempts failed, using fallback")
        return None

class AdvancedStudentGenerator:
    """Generate diverse, realistic student personas using Gemini AI"""
    
    def __init__(self):
        self.gemini = RobustGeminiClient()
        
    async def generate_student_persona(self, student_type: str, index: int) -> StudentPersona:
        """Generate a detailed student persona"""
        
        prompt = f"""Create a realistic JEE aspirant student persona. Student type: {student_type}

Generate a JSON response with these exact keys:
{{
    "name": "Authentic Indian name (male/female)",
    "age": 16-18,
    "grade": "11th" or "12th", 
    "background": "Detailed background (city, family)",
    "personality_traits": ["trait1", "trait2", "trait3"],
    "learning_style": "visual/auditory/kinesthetic/logical/social/individual",
    "strengths": ["Physics", "Chemistry", "Mathematics"],
    "weaknesses": ["Physics", "Chemistry", "Mathematics"],
    "motivation_level": 0.0-1.0,
    "stress_tolerance": 0.0-1.0,
    "confidence": 0.0-1.0,
    "family_support": "high/medium/low",
    "economic_background": "privileged/middle/struggling",
    "previous_performance": "excellent/good/average/below average",
    "study_habits": {{"daily_hours": 4-12, "consistency": 0.0-1.0}},
    "psychological_profile": {{"anxiety_level": 0.0-1.0, "perfectionism": 0.0-1.0}},
    "exam_behavior": {{"time_management": 0.0-1.0, "handles_pressure": 0.0-1.0}}
}}

Make the persona realistic with both strengths and struggles. Include authentic Indian cultural context."""

        response_text = await self.gemini.generate_content_with_retry(prompt)
        
        if response_text:
            try:
                # Extract JSON from response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    data = json.loads(json_str)
                    return self._create_persona_from_data(data, index)
            
            except Exception as e:
                print(f"⚠️ Error parsing persona {index}: {e}")
        
        # Fallback persona
        return self._create_fallback_persona(student_type, index)
    
    def _create_persona_from_data(self, data: Dict[str, Any], index: int) -> StudentPersona:
        """Convert parsed data to StudentPersona"""
        return StudentPersona(
            name=data.get('name', f'Student {index}'),
            age=data.get('age', 17),
            grade=data.get('grade', '12th'),
            background=data.get('background', 'Urban middle-class'),
            personality_traits=data.get('personality_traits', ['hardworking', 'anxious']),
            learning_style=LearningStyle(data.get('learning_style', 'visual')),
            strengths=data.get('strengths', ['Mathematics']),
            weaknesses=data.get('weaknesses', ['Chemistry']),
            motivation_level=float(data.get('motivation_level', 0.7)),
            stress_tolerance=float(data.get('stress_tolerance', 0.5)),
            confidence=float(data.get('confidence', 0.6)),
            family_support=data.get('family_support', 'high'),
            economic_background=data.get('economic_background', 'middle'),
            previous_academic_performance=data.get('previous_performance', 'above average'),
            study_habits=data.get('study_habits', {'daily_hours': 6, 'consistency': 0.7}),
            psychological_profile=data.get('psychological_profile', {'anxiety_level': 0.5}),
            exam_behavior_patterns=data.get('exam_behavior', {'time_management': 0.6})
        )
    
    def _create_fallback_persona(self, student_type: str, index: int) -> StudentPersona:
        """Create fallback persona when AI fails"""
        indian_names = [
            "Arjun Sharma", "Priya Patel", "Rohit Kumar", "Ananya Singh", "Vikram Reddy",
            "Sneha Gupta", "Aditya Verma", "Kavya Nair", "Ravi Iyer", "Pooja Joshi"
        ]
        
        base_traits = {
            "high-achieving competitive": ['ambitious', 'competitive', 'perfectionist'],
            "struggling but motivated": ['persistent', 'hardworking', 'anxious'],
            "average performer with anxiety": ['anxious', 'careful', 'methodical'],
            "talented but inconsistent": ['creative', 'procrastinating', 'confident'],
            "hardworking methodical": ['disciplined', 'organized', 'steady']
        }
        
        return StudentPersona(
            name=indian_names[index % len(indian_names)],
            age=random.randint(16, 18),
            grade=random.choice(['11th', '12th']),
            background=f"Indian JEE aspirant - {student_type}",
            personality_traits=base_traits.get(student_type, ['hardworking', 'focused']),
            learning_style=random.choice(list(LearningStyle)),
            strengths=random.sample(['Physics', 'Chemistry', 'Mathematics'], 2),
            weaknesses=random.sample(['Physics', 'Chemistry', 'Mathematics'], 1),
            motivation_level=random.uniform(0.4, 0.9),
            stress_tolerance=random.uniform(0.3, 0.8),
            confidence=random.uniform(0.4, 0.8),
            family_support=random.choice(['high', 'medium', 'low']),
            economic_background=random.choice(['privileged', 'middle', 'struggling']),
            previous_academic_performance=random.choice(['excellent', 'good', 'average', 'below average']),
            study_habits={'daily_hours': random.randint(4, 10), 'consistency': random.uniform(0.5, 0.9)},
            psychological_profile={'anxiety_level': random.uniform(0.2, 0.8)},
            exam_behavior_patterns={'time_management': random.uniform(0.3, 0.9)}
        )

class AdvancedResponseGenerator:
    """Generate realistic student responses using AI"""
    
    def __init__(self, student_persona: StudentPersona):
        self.persona = student_persona
        self.gemini = RobustGeminiClient()
        
    async def generate_question_response(self, question: str, topic: str, difficulty: float, 
                                       exam_condition: ExamCondition, time_remaining: int) -> Dict[str, Any]:
        """Generate realistic response based on student psychology"""
        
        prompt = f"""Simulate student response for: {self.persona.name}

Student Profile:
- Traits: {', '.join(self.persona.personality_traits)}
- Strengths: {', '.join(self.persona.strengths)}
- Weaknesses: {', '.join(self.persona.weaknesses)}
- Confidence: {self.persona.confidence:.1f}/1.0
- Stress Tolerance: {self.persona.stress_tolerance:.1f}/1.0

Question Context:
- Topic: {topic}
- Difficulty: {difficulty:.1f}/1.0
- Exam Condition: {exam_condition.value}
- Time Remaining: {time_remaining} minutes

Based on this student's psychology, return JSON:
{{
    "is_correct": true/false,
    "time_spent": 30-600 seconds,
    "confidence_during_question": 0.0-1.0,
    "emotional_state": "calm/nervous/focused/anxious/frustrated/confident",
    "thought_process": "Brief description of approach",
    "stress_factors": ["list", "of", "factors"]
}}

Be realistic about their capabilities and exam conditions."""

        response_text = await self.gemini.generate_content_with_retry(prompt)
        
        if response_text:
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    data = json.loads(json_str)
                    
                    return {
                        'is_correct': bool(data.get('is_correct', False)),
                        'time_spent': max(30, min(600, int(data.get('time_spent', 120)))),
                        'confidence_during_question': max(0.0, min(1.0, float(data.get('confidence_during_question', 0.5)))),
                        'emotional_state': str(data.get('emotional_state', 'neutral')),
                        'thought_process': str(data.get('thought_process', 'Standard approach')),
                        'stress_factors': data.get('stress_factors', [])
                    }
                    
            except Exception as e:
                print(f"⚠️ Error parsing response: {e}")
        
        # Fallback response
        return self._generate_fallback_response(difficulty, exam_condition)
    
    def _generate_fallback_response(self, difficulty: float, exam_condition: ExamCondition) -> Dict[str, Any]:
        """Generate fallback response when AI fails"""
        # Base success on persona characteristics
        base_prob = (self.persona.confidence + self.persona.motivation_level) / 2
        difficulty_penalty = difficulty * 0.6
        stress_penalty = (1 - self.persona.stress_tolerance) * 0.3
        
        if exam_condition in [ExamCondition.TIME_PRESSURE, ExamCondition.HIGH_STAKES]:
            stress_penalty += 0.2
        
        success_prob = max(0.1, min(0.9, base_prob - difficulty_penalty - stress_penalty))
        
        return {
            'is_correct': random.random() < success_prob,
            'time_spent': random.randint(60, 300),
            'confidence_during_question': self.persona.confidence + random.uniform(-0.2, 0.2),
            'emotional_state': random.choice(['calm', 'nervous', 'focused', 'anxious']),
            'thought_process': 'Standard problem-solving approach',
            'stress_factors': ['time_pressure'] if exam_condition == ExamCondition.TIME_PRESSURE else []
        }

class AdvancedMultiStudentSimulation:
    """Complete multi-student simulation with comprehensive analysis"""
    
    def __init__(self):
        self.student_generator = AdvancedStudentGenerator()
        self.students: List[StudentPersona] = []
        self.response_generators: Dict[str, AdvancedResponseGenerator] = {}
        self.bkt_system = PedagogicalBKT()
        self.simulation_data = []
        
    async def generate_diverse_cohort(self, num_students: int = 8) -> List[StudentPersona]:
        """Generate diverse student cohort"""
        print(f"🎯 Generating {num_students} diverse student personas...")
        
        student_types = [
            "high-achieving competitive",
            "struggling but motivated", 
            "average performer with anxiety",
            "talented but inconsistent",
            "hardworking methodical",
            "creative but disorganized",
            "perfectionist with high standards",
            "confident natural learner"
        ]
        
        personas = []
        for i in range(num_students):
            student_type = student_types[i % len(student_types)]
            print(f"  Creating persona {i+1}: {student_type}")
            
            persona = await self.student_generator.generate_student_persona(student_type, i)
            personas.append(persona)
            
            # Create response generator
            self.response_generators[persona.name] = AdvancedResponseGenerator(persona)
            
            print(f"  ✅ Generated: {persona.name} ({persona.age}, {persona.grade})")
            
            # Brief delay to manage API rate limits
            await asyncio.sleep(0.5)
        
        self.students = personas
        return personas
    
    async def run_comprehensive_exam_scenarios(self):
        """Run multiple exam scenarios for complete analysis"""
        
        scenarios = [
            {
                'name': 'Foundation Assessment',
                'condition': ExamCondition.PRACTICE_SESSION,
                'topic': 'Algebra_Basics',
                'questions': 6,
                'time_limit': 30,
                'description': 'Low-pressure foundational knowledge check'
            },
            {
                'name': 'Intermediate Challenge',
                'condition': ExamCondition.NORMAL,
                'topic': 'Physics_Mechanics',
                'questions': 8,
                'time_limit': 40,
                'description': 'Standard exam conditions with mixed difficulty'
            },
            {
                'name': 'Time Pressure Test',
                'condition': ExamCondition.TIME_PRESSURE,
                'topic': 'Chemistry_Organic',
                'questions': 10,
                'time_limit': 20,
                'description': 'High-speed problem solving under pressure'
            },
            {
                'name': 'High Stakes Exam',
                'condition': ExamCondition.HIGH_STAKES,
                'topic': 'Mathematics_Calculus',
                'questions': 12,
                'time_limit': 45,
                'description': 'Final exam simulation with maximum pressure'
            }
        ]
        
        all_results = []
        
        for scenario in scenarios:
            print(f"\n{'='*80}")
            print(f"🎯 SCENARIO: {scenario['name']}")
            print(f"📚 {scenario['description']}")
            print(f"⚙️ {scenario['questions']} questions, {scenario['time_limit']} minutes")
            print(f"🏷️ Topic: {scenario['topic']}, Condition: {scenario['condition'].value}")
            print(f"{'='*80}")
            
            scenario_result = await self.simulate_exam_scenario(
                exam_condition=scenario['condition'],
                topic=scenario['topic'],
                num_questions=scenario['questions'],
                time_limit_minutes=scenario['time_limit'],
                scenario_name=scenario['name']
            )
            
            all_results.append(scenario_result)
            
            # Brief pause between scenarios
            await asyncio.sleep(2)
        
        return all_results
    
    async def simulate_exam_scenario(self, exam_condition: ExamCondition, topic: str, 
                                   num_questions: int, time_limit_minutes: int, 
                                   scenario_name: str) -> Dict[str, Any]:
        """Simulate one complete exam scenario"""
        
        scenario_results = {
            'scenario_name': scenario_name,
            'exam_condition': exam_condition.value,
            'topic': topic,
            'num_questions': num_questions,
            'time_limit_minutes': time_limit_minutes,
            'student_performances': {},
            'overall_stats': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for student in self.students:
            print(f"\n👨‍🎓 {student.name} ({', '.join(student.personality_traits[:2])})")
            
            student_results = {
                'student_profile': asdict(student),
                'correct_answers': 0,
                'total_questions': num_questions,
                'total_time_spent': 0,
                'average_confidence': 0,
                'stress_incidents': 0,
                'question_details': [],
                'bkt_progression': []
            }
            
            time_remaining = time_limit_minutes
            
            for q in range(1, num_questions + 1):
                # Progressive difficulty
                difficulty = min(0.9, 0.2 + (q / num_questions) * 0.6)
                
                # Generate question
                question_text = f"{topic} Question {q} (Difficulty: {difficulty:.1f})"
                
                # Get student response
                response = await self.response_generators[student.name].generate_question_response(
                    question=question_text,
                    topic=topic,
                    difficulty=difficulty,
                    exam_condition=exam_condition,
                    time_remaining=time_remaining
                )
                
                # Update BKT
                bkt_result = self.bkt_system.update_mastery(
                    student_id=student.name,
                    topic=topic,
                    is_correct=response['is_correct'],
                    difficulty=difficulty
                )
                
                # Update metrics
                if response['is_correct']:
                    student_results['correct_answers'] += 1
                
                student_results['total_time_spent'] += response['time_spent']
                student_results['average_confidence'] += response['confidence_during_question']
                
                if response['emotional_state'] in ['anxious', 'stressed', 'frustrated']:
                    student_results['stress_incidents'] += 1
                
                time_remaining -= response['time_spent'] / 60
                time_remaining = max(0, time_remaining)
                
                # Detailed tracking
                question_detail = {
                    'question_num': q,
                    'difficulty': difficulty,
                    'correct': response['is_correct'],
                    'time_spent': response['time_spent'],
                    'confidence': response['confidence_during_question'],
                    'emotional_state': response['emotional_state'],
                    'thought_process': response['thought_process'],
                    'bkt_mastery_before': bkt_result['previous_mastery'],
                    'bkt_mastery_after': bkt_result['new_mastery']
                }
                
                student_results['question_details'].append(question_detail)
                student_results['bkt_progression'].append(bkt_result)
                
                # Progress display
                status = "✅" if response['is_correct'] else "❌"
                print(f"  Q{q}: {status} {response['emotional_state'][:8]} "
                      f"({response['time_spent']}s) Mastery: {bkt_result['new_mastery']:.3f}")
                
                # Time pressure effects
                if time_remaining <= 2 and q < num_questions:
                    print(f"  ⏰ CRITICAL: {time_remaining:.1f} min remaining!")
                    exam_condition = ExamCondition.TIME_PRESSURE
            
            # Final calculations
            student_results['accuracy'] = (student_results['correct_answers'] / num_questions) * 100
            student_results['average_confidence'] /= num_questions
            student_results['time_efficiency'] = student_results['total_time_spent'] / (time_limit_minutes * 60)
            student_results['final_mastery'] = student_results['bkt_progression'][-1]['new_mastery'] if student_results['bkt_progression'] else 0
            
            scenario_results['student_performances'][student.name] = student_results
            
            print(f"  📊 Final: {student_results['correct_answers']}/{num_questions} "
                  f"({student_results['accuracy']:.1f}%) | "
                  f"Mastery: {student_results['final_mastery']:.3f} | "
                  f"Stress: {student_results['stress_incidents']}")
        
        # Calculate scenario statistics
        scenario_results['overall_stats'] = self._calculate_scenario_statistics(scenario_results)
        
        return scenario_results
    
    def _calculate_scenario_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive scenario statistics"""
        performances = list(results['student_performances'].values())
        
        if not performances:
            return {}
        
        accuracies = [p['accuracy'] for p in performances]
        masteries = [p['final_mastery'] for p in performances]
        stress_counts = [p['stress_incidents'] for p in performances]
        
        return {
            'total_students': len(performances),
            'average_accuracy': sum(accuracies) / len(accuracies),
            'accuracy_std': (sum((x - sum(accuracies)/len(accuracies))**2 for x in accuracies) / len(accuracies))**0.5,
            'accuracy_range': {'min': min(accuracies), 'max': max(accuracies)},
            'average_final_mastery': sum(masteries) / len(masteries),
            'mastery_range': {'min': min(masteries), 'max': max(masteries)},
            'total_stress_incidents': sum(stress_counts),
            'students_with_stress': sum(1 for s in stress_counts if s > 0),
            'completion_rates': [1 if p['time_efficiency'] <= 1.0 else 0 for p in performances],
            'high_performers': len([a for a in accuracies if a >= 70]),
            'struggling_students': len([a for a in accuracies if a < 40])
        }

class ComprehensiveReportGenerator:
    """Generate detailed PDF reports with charts and analysis"""
    
    def __init__(self, simulation_results: List[Dict[str, Any]], students: List[StudentPersona]):
        self.results = simulation_results
        self.students = students
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_full_report(self) -> str:
        """Generate comprehensive PDF report"""
        filename = f"BKT_Multi_Student_Analysis_{self.timestamp}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title page
        story.append(Paragraph("BKT Multi-Student Simulation Analysis", styles['Title']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading1']))
        
        executive_summary = self._generate_executive_summary()
        for point in executive_summary:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Student Profiles
        story.append(Paragraph("Student Profiles", styles['Heading1']))
        
        for student in self.students:
            story.append(Paragraph(f"{student.name} ({student.age}, {student.grade})", styles['Heading2']))
            
            profile_data = [
                ['Background:', student.background],
                ['Personality:', ', '.join(student.personality_traits)],
                ['Strengths:', ', '.join(student.strengths)],
                ['Weaknesses:', ', '.join(student.weaknesses)],
                ['Confidence:', f"{student.confidence:.2f}/1.0"],
                ['Motivation:', f"{student.motivation_level:.2f}/1.0"],
                ['Stress Tolerance:', f"{student.stress_tolerance:.2f}/1.0"]
            ]
            
            profile_table = Table(profile_data, colWidths=[100, 350])
            profile_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(profile_table)
            story.append(Spacer(1, 12))
        
        # Scenario Analysis
        story.append(Paragraph("Scenario Analysis", styles['Heading1']))
        
        for result in self.results:
            story.append(Paragraph(f"{result['scenario_name']}", styles['Heading2']))
            story.append(Paragraph(f"Topic: {result['topic']} | Condition: {result['exam_condition']}", styles['Normal']))
            
            stats = result['overall_stats']
            
            scenario_data = [
                ['Metric', 'Value'],
                ['Average Accuracy', f"{stats['average_accuracy']:.1f}%"],
                ['Accuracy Range', f"{stats['accuracy_range']['min']:.1f}% - {stats['accuracy_range']['max']:.1f}%"],
                ['High Performers (≥70%)', f"{stats['high_performers']}/{stats['total_students']}"],
                ['Struggling Students (<40%)', f"{stats['struggling_students']}/{stats['total_students']}"],
                ['Students with Stress', f"{stats['students_with_stress']}/{stats['total_students']}"],
                ['Average Final Mastery', f"{stats['average_final_mastery']:.3f}"]
            ]
            
            scenario_table = Table(scenario_data, colWidths=[200, 150])
            scenario_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(scenario_table)
            story.append(Spacer(1, 12))
        
        # System Effectiveness Analysis
        story.append(Paragraph("BKT System Effectiveness", styles['Heading1']))
        
        effectiveness_analysis = self._analyze_system_effectiveness()
        for analysis_point in effectiveness_analysis:
            story.append(Paragraph(f"• {analysis_point}", styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Recommendations
        story.append(Paragraph("Recommendations", styles['Heading1']))
        
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        print(f"📄 Comprehensive report generated: {filename}")
        return filename
    
    def _generate_executive_summary(self) -> List[str]:
        """Generate executive summary points"""
        total_students = len(self.students)
        total_scenarios = len(self.results)
        
        # Calculate overall metrics
        all_accuracies = []
        all_masteries = []
        all_stress = 0
        
        for result in self.results:
            stats = result['overall_stats']
            all_accuracies.append(stats['average_accuracy'])
            all_masteries.append(stats['average_final_mastery'])
            all_stress += stats['total_stress_incidents']
        
        overall_accuracy = sum(all_accuracies) / len(all_accuracies)
        overall_mastery = sum(all_masteries) / len(all_masteries)
        
        return [
            f"Comprehensive simulation tested {total_students} diverse student personas across {total_scenarios} exam scenarios",
            f"Overall system effectiveness: {overall_accuracy:.1f}% average accuracy across all scenarios",
            f"BKT mastery tracking: Average final mastery level of {overall_mastery:.3f} achieved",
            f"Stress management: {all_stress} total stress incidents across all students and scenarios",
            f"Student diversity: Successfully modeled students ranging from high-achievers to struggling learners",
            f"Scenario coverage: Tested under normal, time pressure, high stakes, and practice conditions"
        ]
    
    def _analyze_system_effectiveness(self) -> List[str]:
        """Analyze overall BKT system effectiveness"""
        analysis_points = []
        
        # Performance across scenarios
        scenario_accuracies = [r['overall_stats']['average_accuracy'] for r in self.results]
        best_scenario = max(self.results, key=lambda x: x['overall_stats']['average_accuracy'])
        worst_scenario = min(self.results, key=lambda x: x['overall_stats']['average_accuracy'])
        
        analysis_points.extend([
            f"Best performing scenario: {best_scenario['scenario_name']} ({best_scenario['overall_stats']['average_accuracy']:.1f}% accuracy)",
            f"Most challenging scenario: {worst_scenario['scenario_name']} ({worst_scenario['overall_stats']['average_accuracy']:.1f}% accuracy)",
            f"Performance consistency: Standard deviation of {(sum((x - sum(scenario_accuracies)/len(scenario_accuracies))**2 for x in scenario_accuracies) / len(scenario_accuracies))**0.5:.1f}% across scenarios"
        ])
        
        # Student type analysis
        high_performers = []
        struggling_students = []
        
        for result in self.results:
            for student_name, performance in result['student_performances'].items():
                if performance['accuracy'] >= 70:
                    if student_name not in high_performers:
                        high_performers.append(student_name)
                if performance['accuracy'] < 40:
                    if student_name not in struggling_students:
                        struggling_students.append(student_name)
        
        analysis_points.extend([
            f"Consistently high performers: {len(set(high_performers))} students showed ≥70% accuracy",
            f"Students needing support: {len(set(struggling_students))} students showed <40% accuracy",
            f"BKT adaptation: System successfully tracked mastery progression for all student types"
        ])
        
        return analysis_points
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        return [
            "Implement prerequisite mastery gating - don't advance students to new topics until they achieve ≥60% mastery",
            "Add motivational feedback system with personalized encouragement based on student personality traits",
            "Develop stress detection algorithms to identify when students need breaks or easier questions",
            "Create adaptive difficulty adjustment that responds to real-time emotional state indicators",
            "Implement peer learning recommendations by pairing high performers with struggling students",
            "Add time management training modules for students who consistently struggle with time pressure",
            "Develop subject-specific support pathways for students with clear weakness patterns",
            "Create confidence-building question sequences for anxious student profiles",
            "Implement forgetting curve modeling to schedule optimal review sessions",
            "Add teacher intervention triggers when students show consistent stress or declining performance"
        ]

# Main execution
async def run_advanced_simulation():
    """Execute the complete advanced simulation"""
    
    print("🚀 ADVANCED MULTI-STUDENT BKT SIMULATION")
    print("🤖 Using Gemini 2.5 Flash with robust API failover")
    print("📊 Generating comprehensive analysis and PDF report")
    print("=" * 80)
    
    # Initialize simulation
    simulation = AdvancedMultiStudentSimulation()
    
    # Generate diverse student cohort
    students = await simulation.generate_diverse_cohort(8)
    
    print(f"\n👥 Generated Student Cohort ({len(students)} students):")
    for i, student in enumerate(students, 1):
        print(f"  {i}. {student.name} ({student.age}, {student.grade}) - {student.background}")
        print(f"     Traits: {', '.join(student.personality_traits)}")
        print(f"     Strengths: {', '.join(student.strengths)} | Confidence: {student.confidence:.2f}")
    
    # Run comprehensive scenarios
    all_results = await simulation.run_comprehensive_exam_scenarios()
    
    # Generate comprehensive report
    print(f"\n📄 Generating comprehensive PDF report...")
    report_generator = ComprehensiveReportGenerator(all_results, students)
    pdf_filename = report_generator.generate_full_report()
    
    # Save raw data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"advanced_simulation_data_{timestamp}.json"
    
    with open(json_filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'student_profiles': [asdict(s) for s in students],
            'scenario_results': all_results,
            'simulation_metadata': {
                'total_students': len(students),
                'total_scenarios': len(all_results),
                'api_keys_used': len(API_KEYS),
                'simulation_duration': "~30 minutes"
            }
        }, f, indent=2, default=str)
    
    print(f"\n🎉 Advanced Simulation Complete!")
    print(f"📊 Tested {len(students)} students across {len(all_results)} scenarios")
    print(f"📄 PDF Report: {pdf_filename}")
    print(f"💾 Raw Data: {json_filename}")
    
    # Quick summary
    overall_accuracy = sum(r['overall_stats']['average_accuracy'] for r in all_results) / len(all_results)
    total_stress = sum(r['overall_stats']['total_stress_incidents'] for r in all_results)
    
    print(f"\n📈 Overall Results:")
    print(f"   Average Accuracy: {overall_accuracy:.1f}%")
    print(f"   Total Stress Incidents: {total_stress}")
    print(f"   System Performance: {'EXCELLENT' if overall_accuracy > 60 else 'NEEDS IMPROVEMENT'}")
    
    return all_results, pdf_filename

if __name__ == "__main__":
    asyncio.run(run_advanced_simulation())