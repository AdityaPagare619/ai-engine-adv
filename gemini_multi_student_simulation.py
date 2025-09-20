#!/usr/bin/env python3
"""
Gemini AI-Powered Multi-Student Simulation System
Creates realistic student personas with authentic behaviors and learning patterns
Uses Google Gemini 2.5 Pro to generate diverse student profiles and responses
"""

import google.generativeai as genai
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import concurrent.futures

# Configure Gemini API (rotating through provided keys)
API_KEYS = [
    "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
    "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
    "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM"
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
    family_support: str  # "high", "medium", "low"
    economic_background: str  # "privileged", "middle", "struggling"
    previous_academic_performance: str
    study_habits: Dict[str, Any]
    psychological_profile: Dict[str, Any]
    exam_behavior_patterns: Dict[str, Any]

class GeminiStudentGenerator:
    """Generates authentic student personas using Gemini AI"""
    
    def __init__(self):
        self.current_key_index = 0
        self.model = None
        self._setup_gemini()
        
    def _setup_gemini(self):
        """Initialize Gemini with rotating API keys"""
        try:
            genai.configure(api_key=API_KEYS[self.current_key_index])
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print(f"✅ Gemini initialized with API key {self.current_key_index + 1}")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self._rotate_api_key()
    
    def _rotate_api_key(self):
        """Switch to next API key if current one fails"""
        self.current_key_index = (self.current_key_index + 1) % len(API_KEYS)
        genai.configure(api_key=API_KEYS[self.current_key_index])
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print(f"🔄 Switched to API key {self.current_key_index + 1}")
    
    async def generate_student_persona(self, student_type: str = "diverse") -> StudentPersona:
        """Generate a realistic student persona using Gemini AI"""
        
        prompt = f"""
        Create a highly realistic and detailed student persona for educational simulation. 
        The student should be a {student_type} Indian JEE aspirant preparing for engineering entrance exams.
        
        Generate a complete psychological and academic profile including:
        
        1. Basic Demographics:
        - Name (authentic Indian name)
        - Age (16-18)
        - Grade (11th or 12th)
        - City/background
        
        2. Personality & Psychology:
        - 3-5 personality traits (realistic combinations)
        - Learning style preference
        - Confidence level (0.0-1.0)
        - Stress tolerance (0.0-1.0)
        - Motivation level (0.0-1.0)
        
        3. Academic Background:
        - Subject strengths (Physics, Chemistry, Math)
        - Subject weaknesses
        - Previous academic performance
        - Study habits and patterns
        
        4. Social Context:
        - Family support level
        - Economic background
        - Social pressures
        - Career aspirations
        
        5. Exam Behavior:
        - How they handle time pressure
        - Response to difficult questions
        - Anxiety patterns
        - Mistake-making tendencies
        
        Make the persona authentic, complex, and relatable. Include both strengths and realistic struggles.
        Return the response as a structured JSON format.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse Gemini response and convert to StudentPersona
            persona_data = self._parse_gemini_response(response.text)
            return self._create_student_persona(persona_data)
            
        except Exception as e:
            print(f"❌ Error generating persona: {e}")
            self._rotate_api_key()
            # Fallback to predefined persona
            return self._create_fallback_persona()
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and clean Gemini response"""
        try:
            # Extract JSON from response (Gemini sometimes adds extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"⚠️ Failed to parse Gemini response: {e}")
            # Return structured fallback data
            return self._get_fallback_data()
    
    def _create_student_persona(self, data: Dict[str, Any]) -> StudentPersona:
        """Convert parsed data to StudentPersona object"""
        try:
            return StudentPersona(
                name=data.get('name', 'Generated Student'),
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
                study_habits=data.get('study_habits', {}),
                psychological_profile=data.get('psychological_profile', {}),
                exam_behavior_patterns=data.get('exam_behavior', {})
            )
        except Exception as e:
            print(f"⚠️ Error creating persona: {e}")
            return self._create_fallback_persona()
    
    def _create_fallback_persona(self) -> StudentPersona:
        """Create a fallback persona when Gemini fails"""
        fallback_names = ["Arjun Sharma", "Priya Patel", "Rohit Kumar", "Ananya Singh", "Vikram Reddy"]
        
        return StudentPersona(
            name=random.choice(fallback_names),
            age=random.randint(16, 18),
            grade=random.choice(['11th', '12th']),
            background="Indian JEE aspirant",
            personality_traits=random.sample(['hardworking', 'anxious', 'confident', 'perfectionist', 'social'], 3),
            learning_style=random.choice(list(LearningStyle)),
            strengths=random.sample(['Physics', 'Chemistry', 'Mathematics'], 2),
            weaknesses=random.sample(['Physics', 'Chemistry', 'Mathematics'], 1),
            motivation_level=random.uniform(0.4, 0.9),
            stress_tolerance=random.uniform(0.3, 0.8),
            confidence=random.uniform(0.4, 0.8),
            family_support=random.choice(['high', 'medium', 'low']),
            economic_background=random.choice(['privileged', 'middle', 'struggling']),
            previous_academic_performance=random.choice(['excellent', 'good', 'average', 'below average']),
            study_habits={'daily_hours': random.randint(4, 12), 'consistency': random.uniform(0.5, 0.9)},
            psychological_profile={'anxiety_level': random.uniform(0.2, 0.8)},
            exam_behavior_patterns={'time_management': random.uniform(0.3, 0.9)}
        )
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data structure"""
        return {
            'name': 'AI Generated Student',
            'age': 17,
            'grade': '12th',
            'background': 'Urban middle-class',
            'personality_traits': ['hardworking', 'anxious'],
            'learning_style': 'visual',
            'strengths': ['Mathematics'],
            'weaknesses': ['Chemistry'],
            'motivation_level': 0.7,
            'stress_tolerance': 0.5,
            'confidence': 0.6,
            'family_support': 'high',
            'economic_background': 'middle',
            'previous_performance': 'above average',
            'study_habits': {'daily_hours': 6, 'consistency': 0.7},
            'psychological_profile': {'anxiety_level': 0.5},
            'exam_behavior': {'time_management': 0.6}
        }

class GeminiResponseGenerator:
    """Generates realistic student responses using Gemini AI"""
    
    def __init__(self, student_persona: StudentPersona):
        self.persona = student_persona
        self.generator = GeminiStudentGenerator()
        
    async def generate_question_response(self, question: str, topic: str, difficulty: float, 
                                       exam_condition: ExamCondition, time_remaining: int) -> Dict[str, Any]:
        """Generate realistic response to a question based on student persona"""
        
        persona_context = f"""
        Student Profile:
        - Name: {self.persona.name}
        - Personality: {', '.join(self.persona.personality_traits)}
        - Strengths: {', '.join(self.persona.strengths)}
        - Weaknesses: {', '.join(self.persona.weaknesses)}
        - Confidence: {self.persona.confidence:.1f}/1.0
        - Stress Tolerance: {self.persona.stress_tolerance:.1f}/1.0
        - Motivation: {self.persona.motivation_level:.1f}/1.0
        """
        
        prompt = f"""
        {persona_context}
        
        Current Situation:
        - Question Topic: {topic}
        - Question Difficulty: {difficulty:.1f}/1.0
        - Exam Condition: {exam_condition.value}
        - Time Remaining: {time_remaining} minutes
        
        Question: {question}
        
        Based on this student's profile, simulate their realistic response including:
        1. Would they get this question correct? (true/false)
        2. How long would they spend on it? (in seconds)
        3. Their confidence level while answering (0.0-1.0)
        4. Their emotional state during the question
        5. Their thought process and approach
        6. Any anxiety or stress factors affecting performance
        
        Be realistic about their capabilities and limitations. Consider:
        - Their subject strengths/weaknesses
        - Current stress level and exam conditions
        - Time pressure effects
        - Their personality traits influencing performance
        
        Return as structured JSON with keys: is_correct, time_spent, confidence_during_question, emotional_state, thought_process, stress_factors
        """
        
        try:
            response = self.generator.model.generate_content(prompt)
            return self._parse_response_data(response.text)
            
        except Exception as e:
            print(f"❌ Error generating response for {self.persona.name}: {e}")
            self.generator._rotate_api_key()
            return self._generate_fallback_response(difficulty, exam_condition)
    
    def _parse_response_data(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response for question answering"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Validate and sanitize data
                return {
                    'is_correct': bool(data.get('is_correct', False)),
                    'time_spent': max(10, min(600, int(data.get('time_spent', 120)))),  # 10sec to 10min
                    'confidence_during_question': max(0.0, min(1.0, float(data.get('confidence_during_question', 0.5)))),
                    'emotional_state': str(data.get('emotional_state', 'neutral')),
                    'thought_process': str(data.get('thought_process', 'Standard approach')),
                    'stress_factors': data.get('stress_factors', [])
                }
            else:
                raise ValueError("No valid JSON in response")
                
        except Exception as e:
            print(f"⚠️ Failed to parse response: {e}")
            return self._generate_fallback_response(0.5, ExamCondition.NORMAL)
    
    def _generate_fallback_response(self, difficulty: float, exam_condition: ExamCondition) -> Dict[str, Any]:
        """Generate fallback response when Gemini fails"""
        # Base success probability on persona and difficulty
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

class MultiStudentSimulation:
    """Advanced multi-student simulation with diverse scenarios"""
    
    def __init__(self):
        self.student_generator = GeminiStudentGenerator()
        self.students: List[StudentPersona] = []
        self.response_generators: Dict[str, GeminiResponseGenerator] = {}
        self.simulation_data = []
        
        # Enhanced BKT system from previous code
        from enhanced_bkt_system import PedagogicalBKT
        self.bkt_system = PedagogicalBKT()
    
    async def generate_diverse_student_cohort(self, num_students: int = 5) -> List[StudentPersona]:
        """Generate a diverse group of students with varied backgrounds"""
        print(f"🎯 Generating {num_students} diverse student personas using Gemini AI...")
        
        student_types = [
            "high-achieving competitive",
            "struggling but motivated", 
            "average performer with anxiety",
            "talented but inconsistent",
            "hardworking methodical"
        ]
        
        tasks = []
        for i in range(num_students):
            student_type = student_types[i % len(student_types)]
            task = self.student_generator.generate_student_persona(student_type)
            tasks.append(task)
        
        # Generate personas concurrently
        personas = []
        for i, task in enumerate(tasks):
            try:
                persona = await task
                personas.append(persona)
                print(f"✅ Generated persona {i+1}: {persona.name}")
                
                # Create response generator for this student
                self.response_generators[persona.name] = GeminiResponseGenerator(persona)
                
                # Small delay to avoid API rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Failed to generate persona {i+1}: {e}")
        
        self.students = personas
        return personas
    
    async def simulate_exam_scenario(self, exam_condition: ExamCondition, 
                                   topic: str = "Physics_Mechanics", 
                                   num_questions: int = 10,
                                   time_limit_minutes: int = 60):
        """Simulate an exam scenario with multiple students"""
        
        print(f"\n🎯 Starting Exam Simulation: {exam_condition.value.upper()}")
        print(f"📚 Topic: {topic} | Questions: {num_questions} | Time: {time_limit_minutes} minutes")
        print("=" * 80)
        
        scenario_results = {
            'exam_condition': exam_condition.value,
            'topic': topic,
            'student_performances': {},
            'overall_stats': {},
            'insights': []
        }
        
        # Simulate each student
        for student in self.students:
            print(f"\n👨‍🎓 {student.name} ({', '.join(student.personality_traits)})")
            
            student_results = {
                'correct_answers': 0,
                'total_questions': num_questions,
                'total_time_spent': 0,
                'average_confidence': 0,
                'stress_incidents': 0,
                'question_details': []
            }
            
            time_remaining = time_limit_minutes
            
            for q in range(1, num_questions + 1):
                # Generate question difficulty (progressive)
                difficulty = min(0.9, 0.3 + (q / num_questions) * 0.5)
                
                # Generate response using Gemini
                question = f"Question {q} on {topic} (Difficulty: {difficulty:.1f})"
                
                response = await self.response_generators[student.name].generate_question_response(
                    question=question,
                    topic=topic, 
                    difficulty=difficulty,
                    exam_condition=exam_condition,
                    time_remaining=time_remaining
                )
                
                # Update BKT system
                bkt_result = self.bkt_system.update_mastery(
                    student_id=student.name,
                    topic=topic,
                    is_correct=response['is_correct'],
                    difficulty=difficulty
                )
                
                # Track results
                if response['is_correct']:
                    student_results['correct_answers'] += 1
                
                student_results['total_time_spent'] += response['time_spent']
                student_results['average_confidence'] += response['confidence_during_question']
                
                if response['emotional_state'] in ['anxious', 'stressed', 'overwhelmed']:
                    student_results['stress_incidents'] += 1
                
                time_remaining -= response['time_spent'] / 60  # Convert seconds to minutes
                time_remaining = max(0, time_remaining)
                
                # Detailed question tracking
                student_results['question_details'].append({
                    'question_num': q,
                    'difficulty': difficulty,
                    'correct': response['is_correct'],
                    'time_spent': response['time_spent'],
                    'confidence': response['confidence_during_question'],
                    'emotional_state': response['emotional_state'],
                    'bkt_mastery_after': bkt_result['new_mastery']
                })
                
                # Show progress
                status = "✅" if response['is_correct'] else "❌"
                print(f"  Q{q}: {status} ({response['emotional_state']}, {response['time_spent']}s, Mastery: {bkt_result['new_mastery']:.3f})")
                
                # Time pressure effects
                if time_remaining <= 5 and q < num_questions:
                    print(f"  ⏰ Time pressure! {time_remaining:.1f} minutes remaining")
                    exam_condition = ExamCondition.TIME_PRESSURE
            
            # Calculate final metrics
            student_results['accuracy'] = (student_results['correct_answers'] / num_questions) * 100
            student_results['average_confidence'] /= num_questions
            student_results['time_efficiency'] = student_results['total_time_spent'] / (time_limit_minutes * 60)
            
            scenario_results['student_performances'][student.name] = student_results
            
            print(f"  📊 Final: {student_results['correct_answers']}/{num_questions} ({student_results['accuracy']:.1f}%)")
            print(f"  ⏱️ Time: {student_results['total_time_spent']//60:.0f}m {student_results['total_time_spent']%60:.0f}s")
        
        # Generate overall insights
        scenario_results['overall_stats'] = self._calculate_scenario_stats(scenario_results)
        scenario_results['insights'] = await self._generate_scenario_insights(scenario_results)
        
        return scenario_results
    
    def _calculate_scenario_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall statistics for the scenario"""
        performances = list(results['student_performances'].values())
        
        return {
            'average_accuracy': sum(p['accuracy'] for p in performances) / len(performances),
            'accuracy_range': {
                'min': min(p['accuracy'] for p in performances),
                'max': max(p['accuracy'] for p in performances)
            },
            'average_confidence': sum(p['average_confidence'] for p in performances) / len(performances),
            'total_stress_incidents': sum(p['stress_incidents'] for p in performances),
            'completion_rates': [
                1.0 if p['time_efficiency'] <= 1.0 else 0.0 for p in performances
            ]
        }
    
    async def _generate_scenario_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate insights about the scenario using Gemini"""
        
        summary = f"""
        Exam Scenario Analysis:
        - Condition: {results['exam_condition']}
        - Topic: {results['topic']}
        - Average Accuracy: {results['overall_stats']['average_accuracy']:.1f}%
        - Stress Incidents: {results['overall_stats']['total_stress_incidents']}
        
        Student Performances:
        """
        
        for name, perf in results['student_performances'].items():
            summary += f"- {name}: {perf['accuracy']:.1f}% accuracy, {perf['stress_incidents']} stress incidents\n"
        
        prompt = f"""
        {summary}
        
        Based on this exam simulation data, provide 3-5 key insights about:
        1. How different student types performed under these conditions
        2. The impact of the exam condition on performance
        3. Recommendations for improving student outcomes
        4. Patterns in stress and time management
        
        Return as a JSON array of insight strings.
        """
        
        try:
            response = self.student_generator.model.generate_content(prompt)
            insights_text = response.text
            
            # Extract JSON array
            start_idx = insights_text.find('[')
            end_idx = insights_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                insights_json = insights_text[start_idx:end_idx]
                return json.loads(insights_json)
            else:
                return ["Performance varied significantly based on student personality types",
                       "Exam conditions had measurable impact on stress levels",
                       "Time management skills correlated with overall performance"]
                
        except Exception as e:
            print(f"⚠️ Failed to generate insights: {e}")
            return ["Simulation completed successfully with diverse student responses"]

# Demo and testing
async def run_comprehensive_simulation():
    """Run a comprehensive multi-student simulation"""
    
    print("🚀 GEMINI-POWERED MULTI-STUDENT SIMULATION")
    print("=" * 80)
    
    # Initialize simulation
    simulation = MultiStudentSimulation()
    
    # Generate diverse student cohort
    students = await simulation.generate_diverse_student_cohort(5)
    
    # Print student profiles
    print(f"\n👥 Generated Student Cohort:")
    for student in students:
        print(f"  📋 {student.name} ({student.age}, {student.grade})")
        print(f"      Background: {student.background}")
        print(f"      Traits: {', '.join(student.personality_traits)}")
        print(f"      Strengths: {', '.join(student.strengths)}")
        print(f"      Confidence: {student.confidence:.1f}, Motivation: {student.motivation_level:.1f}")
    
    # Run different exam scenarios
    scenarios = [
        (ExamCondition.PRACTICE_SESSION, "Algebra_Basics", 5, 30),
        (ExamCondition.TIME_PRESSURE, "Physics_Mechanics", 8, 20),
        (ExamCondition.HIGH_STAKES, "Chemistry_Organic", 10, 45)
    ]
    
    all_results = []
    
    for condition, topic, questions, time_limit in scenarios:
        print(f"\n" + "="*60)
        results = await simulation.simulate_exam_scenario(
            exam_condition=condition,
            topic=topic,
            num_questions=questions,
            time_limit_minutes=time_limit
        )
        
        all_results.append(results)
        
        # Show scenario insights
        print(f"\n💡 Scenario Insights:")
        for insight in results['insights']:
            print(f"  • {insight}")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gemini_multi_student_simulation_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'simulation_timestamp': timestamp,
            'student_profiles': [asdict(s) for s in students],
            'scenario_results': all_results,
            'summary': {
                'total_students': len(students),
                'total_scenarios': len(scenarios),
                'total_questions': sum(len(r['student_performances']) * 
                                     r['student_performances'][list(r['student_performances'].keys())[0]]['total_questions'] 
                                     for r in all_results)
            }
        }, f, indent=2, default=str)
    
    print(f"\n📁 Complete simulation results saved to: {filename}")
    print(f"🎯 Simulation Summary:")
    print(f"   Students: {len(students)}")
    print(f"   Scenarios: {len(scenarios)}")
    print(f"   Total Interactions: {sum(len(r['student_performances']) for r in all_results)}")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_simulation())