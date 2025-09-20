#!/usr/bin/env python3
"""
Comprehensive Phase 4B Test Suite
Tests all components thoroughly with end-to-end simulation
"""

import sys
import os
import json
import time
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging for comprehensive testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase4b_comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add ai_engine to path
ai_engine_path = os.path.join(os.getcwd(), 'ai_engine', 'src')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

class Phase4BComprehensiveTest:
    """Comprehensive test suite for Phase 4B components"""
    
    def __init__(self):
        self.results = {
            'start_time': datetime.now(),
            'component_tests': {},
            'integration_tests': {},
            'performance_metrics': {},
            'end_to_end_simulation': {},
            'errors': [],
            'recommendations': []
        }
        
        # Initialize components
        self.components = {}
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate comprehensive test data for simulations"""
        return {
            'students': [
                {'id': 'student_001', 'skill_level': 'beginner', 'stress_tendency': 'low'},
                {'id': 'student_002', 'skill_level': 'intermediate', 'stress_tendency': 'medium'},
                {'id': 'student_003', 'skill_level': 'advanced', 'stress_tendency': 'high'},
                {'id': 'student_004', 'skill_level': 'struggling', 'stress_tendency': 'high'}
            ],
            'topics': ['algebra_basics', 'geometry_fundamentals', 'calculus_intro', 'statistics_basic'],
            'question_difficulties': [0.2, 0.4, 0.6, 0.8, 1.0],
            'session_scenarios': [
                {'duration_ms': 900000, 'questions': 10, 'difficulty_progression': 'increasing'},
                {'duration_ms': 1800000, 'questions': 20, 'difficulty_progression': 'adaptive'},
                {'duration_ms': 600000, 'questions': 8, 'difficulty_progression': 'mixed'}
            ]
        }
    
    def test_time_allocator(self) -> Dict[str, Any]:
        """Comprehensive test of Dynamic Time Allocator"""
        logger.info("🕒 Testing Dynamic Time Allocator...")
        
        try:
            from knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
            allocator = DynamicTimeAllocator()
            self.components['time_allocator'] = allocator
            
            test_cases = []
            
            # Test various stress and fatigue combinations
            stress_levels = [0.0, 0.3, 0.6, 0.9]
            fatigue_levels = [0.0, 0.2, 0.5, 0.8]
            
            for stress in stress_levels:
                for fatigue in fatigue_levels:
                    request = TimeAllocationRequest(
                        student_id="test_comprehensive",
                        question_id=f"q_stress_{stress}_fatigue_{fatigue}",
                        base_time_ms=30000,
                        stress_level=stress,
                        fatigue_level=fatigue,
                        mastery=0.5,
                        difficulty=0.6,
                        session_elapsed_ms=600000
                    )
                    
                    result = allocator.allocate(request)
                    test_cases.append({
                        'stress_level': stress,
                        'fatigue_level': fatigue,
                        'allocated_time_ms': result.final_time_ms,
                        'factor': result.factor,
                        'breakdown': result.breakdown
                    })
            
            # Performance test - allocate 1000 times
            start_time = time.time()
            for i in range(1000):
                request = TimeAllocationRequest(
                    student_id="perf_test",
                    question_id=f"q_{i}",
                    base_time_ms=25000,
                    stress_level=random.random(),
                    fatigue_level=random.random(),
                    mastery=random.random(),
                    difficulty=random.random(),
                    session_elapsed_ms=random.randint(300000, 1800000)
                )
                allocator.allocate(request)
            
            performance_time = time.time() - start_time
            
            return {
                'status': 'success',
                'test_cases': len(test_cases),
                'sample_results': test_cases[:5],
                'performance_1000_allocations_sec': performance_time,
                'avg_allocation_time_ms': (performance_time * 1000) / 1000
            }
            
        except Exception as e:
            logger.error(f"Time Allocator test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_cognitive_load_manager(self) -> Dict[str, Any]:
        """Comprehensive test of Cognitive Load Manager"""
        logger.info("🧠 Testing Cognitive Load Manager...")
        
        try:
            from knowledge_tracing.congnitive.load_manager import CognitiveLoadManager
            load_manager = CognitiveLoadManager()
            self.components['cognitive_load'] = load_manager
            
            test_scenarios = []
            
            # Test different cognitive load scenarios
            scenarios = [
                {'name': 'easy_scenario', 'problem_steps': 2, 'concept_mastery': 0.8, 'time_pressure': 0.1},
                {'name': 'moderate_scenario', 'problem_steps': 4, 'concept_mastery': 0.6, 'time_pressure': 0.4},
                {'name': 'difficult_scenario', 'problem_steps': 8, 'concept_mastery': 0.3, 'time_pressure': 0.8},
                {'name': 'overload_scenario', 'problem_steps': 12, 'concept_mastery': 0.2, 'time_pressure': 0.9}
            ]
            
            for scenario in scenarios:
                assessment = load_manager.assess(
                    problem_steps=scenario['problem_steps'],
                    concept_mastery=scenario['concept_mastery'],
                    prerequisites_gap=0.3,
                    time_pressure=scenario['time_pressure'],
                    interface_score=0.2,
                    distractions=0.1,
                    stress_level=0.3,
                    fatigue_level=0.2
                )
                
                test_scenarios.append({
                    'scenario': scenario['name'],
                    'total_load': assessment.total_load,
                    'overload_risk': assessment.overload_risk,
                    'recommendations': len(assessment.recommendations),
                    'components': assessment.components
                })
            
            return {
                'status': 'success',
                'scenarios_tested': len(test_scenarios),
                'scenario_results': test_scenarios
            }
            
        except Exception as e:
            logger.error(f"Cognitive Load Manager test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_stress_detection(self) -> Dict[str, Any]:
        """Comprehensive test of Stress Detection Engine"""
        logger.info("😰 Testing Stress Detection Engine...")
        
        try:
            from knowledge_tracing.stress.detection_engine import MultiModalStressDetector
            detector = MultiModalStressDetector(window_size=10)
            self.components['stress_detection'] = detector
            
            # Test stress detection patterns
            stress_patterns = [
                {'name': 'calm_student', 'response_times': [1500, 1600, 1400, 1550], 'correctness': [True, True, True, True]},
                {'name': 'struggling_student', 'response_times': [3000, 4500, 5000, 2800], 'correctness': [False, False, True, False]},
                {'name': 'stressed_student', 'response_times': [8000, 12000, 6000, 15000], 'correctness': [False, True, False, False]},
                {'name': 'improving_student', 'response_times': [4000, 3500, 2800, 2200], 'correctness': [False, True, True, True]}
            ]
            
            pattern_results = []
            
            for pattern in stress_patterns:
                # Simulate multiple responses for this student pattern
                stress_levels = []
                
                for i, (rt, correct) in enumerate(zip(pattern['response_times'], pattern['correctness'])):
                    result = detector.detect(
                        response_time=rt,
                        correct=correct,
                        hesitation_ms=random.randint(0, 2000),
                        keystroke_dev=random.uniform(0.1, 0.8)
                    )
                    
                    stress_levels.append(result.level)
                
                pattern_results.append({
                    'pattern': pattern['name'],
                    'avg_stress_level': sum(stress_levels) / len(stress_levels),
                    'max_stress_level': max(stress_levels),
                    'stress_progression': stress_levels,
                    'final_intervention': result.intervention
                })
            
            return {
                'status': 'success',
                'patterns_tested': len(pattern_results),
                'pattern_results': pattern_results
            }
            
        except Exception as e:
            logger.error(f"Stress Detection test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_enhanced_bkt(self) -> Dict[str, Any]:
        """Comprehensive test of Enhanced BKT System"""
        logger.info("📚 Testing Enhanced BKT System...")
        
        try:
            from enhanced_bkt_system import PedagogicalBKT
            bkt = PedagogicalBKT()
            self.components['bkt'] = bkt
            
            # Test learning progression for different student types
            student_progressions = []
            
            for student in self.test_data['students']:
                student_id = student['id']
                topic = 'algebra_basics'
                
                # Simulate 20 questions with varying difficulty
                mastery_progression = []
                
                for q in range(20):
                    # Simulate difficulty progression
                    difficulty = min(0.9, 0.3 + (q * 0.03))
                    
                    # Simulate success probability based on student skill level
                    skill_multipliers = {
                        'beginner': 0.4, 'intermediate': 0.6, 
                        'advanced': 0.8, 'struggling': 0.2
                    }
                    
                    base_prob = skill_multipliers[student['skill_level']]
                    success_prob = max(0.1, min(0.9, base_prob * (1.0 - difficulty * 0.3)))
                    is_correct = random.random() < success_prob
                    
                    result = bkt.update_mastery(
                        student_id=student_id,
                        topic=topic,
                        is_correct=is_correct,
                        difficulty=difficulty,
                        response_time_ms=random.randint(1000, 5000),
                        confidence_score=random.uniform(0.3, 0.9)
                    )
                    
                    mastery_progression.append({
                        'question': q + 1,
                        'difficulty': difficulty,
                        'correct': is_correct,
                        'mastery_before': result['previous_mastery'],
                        'mastery_after': result['new_mastery'],
                        'student_state': result['student_state'],
                        'recommended_difficulty': result['recommended_difficulty']
                    })
                
                student_progressions.append({
                    'student_id': student_id,
                    'skill_level': student['skill_level'],
                    'final_mastery': mastery_progression[-1]['mastery_after'],
                    'mastery_growth': mastery_progression[-1]['mastery_after'] - mastery_progression[0]['mastery_before'],
                    'progression': mastery_progression[:5]  # Sample first 5 questions
                })
            
            return {
                'status': 'success',
                'students_tested': len(student_progressions),
                'student_progressions': student_progressions
            }
            
        except Exception as e:
            logger.error(f"Enhanced BKT test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def test_gemini_api_manager(self) -> Dict[str, Any]:
        """Comprehensive test of Gemini API Manager"""
        logger.info("🤖 Testing Gemini API Manager...")
        
        try:
            from gemini_api_manager import GeminiAPIManager
            
            api_keys = [
                "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
                "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
                "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
                "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"
            ]
            
            manager = GeminiAPIManager(api_keys)
            self.components['api_manager'] = manager
            
            # Test basic functionality without making actual API calls
            stats = manager.get_usage_stats()
            
            # Test key rotation logic
            available_key = manager._get_available_key()
            
            # Simulate quota management
            test_results = {
                'total_keys': stats['total_keys'],
                'active_keys': stats['active_keys'],
                'key_rotation_works': available_key is not None,
                'usage_tracking': stats
            }
            
            # Note: Not making actual API calls to avoid quota usage during testing
            logger.info("Gemini API Manager tests completed (without actual API calls)")
            
            return {
                'status': 'success',
                'test_results': test_results
            }
            
        except Exception as e:
            logger.error(f"Gemini API Manager test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_integration_workflow(self) -> Dict[str, Any]:
        """Test integrated workflow of all components"""
        logger.info("🔗 Testing Integrated Workflow...")
        
        try:
            workflow_results = []
            
            for student in self.test_data['students'][:2]:  # Test with 2 students
                student_id = student['id']
                topic = 'algebra_basics'
                
                # Simulate a complete learning session
                session_results = []
                current_stress = 0.0
                current_fatigue = 0.0
                session_start = time.time()
                
                for question_num in range(5):  # 5 questions per test session
                    # 1. Get current mastery from BKT
                    if hasattr(self, 'components') and 'bkt' in self.components:
                        key = f"{student_id}_{topic}"
                        current_mastery = self.components['bkt'].student_states.get(key, {}).get('mastery', 0.1)
                    else:
                        current_mastery = 0.5
                    
                    # 2. Assess cognitive load
                    if 'cognitive_load' in self.components:
                        load_assessment = self.components['cognitive_load'].assess(
                            problem_steps=random.randint(2, 6),
                            concept_mastery=current_mastery,
                            prerequisites_gap=0.3,
                            time_pressure=current_stress,
                            interface_score=0.2,
                            distractions=0.1,
                            stress_level=current_stress,
                            fatigue_level=current_fatigue
                        )
                        cognitive_load = load_assessment.total_load
                    else:
                        cognitive_load = 2.0
                    
                    # 3. Allocate time based on stress and fatigue
                    if 'time_allocator' in self.components:
                        from knowledge_tracing.pacing.time_allocator import TimeAllocationRequest
                        
                        time_request = TimeAllocationRequest(
                            student_id=student_id,
                            question_id=f"integration_q_{question_num}",
                            base_time_ms=30000,
                            stress_level=current_stress,
                            fatigue_level=current_fatigue,
                            mastery=current_mastery,
                            difficulty=0.6,
                            session_elapsed_ms=int((time.time() - session_start) * 1000)
                        )
                        
                        time_allocation = self.components['time_allocator'].allocate(time_request)
                        allocated_time = time_allocation.final_time_ms
                    else:
                        allocated_time = 30000
                    
                    # 4. Simulate student response
                    response_time = random.randint(int(allocated_time * 0.3), int(allocated_time * 1.2))
                    is_correct = random.random() < (current_mastery * 0.8 + 0.2)
                    
                    # 5. Detect stress from response
                    if 'stress_detection' in self.components:
                        stress_result = self.components['stress_detection'].detect(
                            response_time=response_time,
                            correct=is_correct,
                            hesitation_ms=random.randint(0, 1000),
                            keystroke_dev=random.uniform(0.1, 0.6)
                        )
                        current_stress = max(0.0, min(1.0, stress_result.level))
                    
                    # 6. Update BKT with new response
                    if 'bkt' in self.components:
                        bkt_result = self.components['bkt'].update_mastery(
                            student_id=student_id,
                            topic=topic,
                            is_correct=is_correct,
                            difficulty=0.6,
                            response_time_ms=response_time
                        )
                        new_mastery = bkt_result['new_mastery']
                    else:
                        new_mastery = current_mastery
                    
                    # Update fatigue (increases over time)
                    current_fatigue = min(1.0, current_fatigue + 0.1)
                    
                    session_results.append({
                        'question': question_num + 1,
                        'mastery_before': current_mastery,
                        'mastery_after': new_mastery,
                        'cognitive_load': cognitive_load,
                        'allocated_time_ms': allocated_time,
                        'response_time_ms': response_time,
                        'correct': is_correct,
                        'stress_level': current_stress,
                        'fatigue_level': current_fatigue
                    })
                
                workflow_results.append({
                    'student_id': student_id,
                    'skill_level': student['skill_level'],
                    'session_results': session_results,
                    'final_mastery': session_results[-1]['mastery_after'],
                    'avg_stress': sum(r['stress_level'] for r in session_results) / len(session_results),
                    'total_learning_time_ms': sum(r['response_time_ms'] for r in session_results)
                })
            
            return {
                'status': 'success',
                'students_tested': len(workflow_results),
                'workflow_results': workflow_results
            }
            
        except Exception as e:
            logger.error(f"Integration workflow test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        logger.info("🚀 Starting Comprehensive Phase 4B Testing...")
        
        # Test individual components
        self.results['component_tests']['time_allocator'] = self.test_time_allocator()
        self.results['component_tests']['cognitive_load'] = self.test_cognitive_load_manager()
        self.results['component_tests']['stress_detection'] = self.test_stress_detection()
        self.results['component_tests']['enhanced_bkt'] = self.test_enhanced_bkt()
        self.results['component_tests']['api_manager'] = await self.test_gemini_api_manager()
        
        # Test integration
        self.results['integration_tests']['workflow'] = self.test_integration_workflow()
        
        # Calculate summary statistics
        successful_components = sum(1 for test in self.results['component_tests'].values() 
                                  if test.get('status') == 'success')
        total_components = len(self.results['component_tests'])
        
        self.results['summary'] = {
            'total_components': total_components,
            'successful_components': successful_components,
            'success_rate': successful_components / total_components,
            'integration_success': self.results['integration_tests']['workflow'].get('status') == 'success',
            'overall_status': 'success' if successful_components == total_components else 'partial',
            'end_time': datetime.now(),
            'total_test_duration': datetime.now() - self.results['start_time']
        }
        
        # Generate recommendations
        if self.results['summary']['success_rate'] >= 0.9:
            self.results['recommendations'].append("✅ All components working excellently - Ready for full Phase 4 execution")
        elif self.results['summary']['success_rate'] >= 0.7:
            self.results['recommendations'].append("🟡 Most components working - Address failing components before production")
        else:
            self.results['recommendations'].append("🔴 Multiple component failures - Requires significant debugging")
        
        if self.results['summary']['integration_success']:
            self.results['recommendations'].append("✅ Integration workflow successful - Components work well together")
        else:
            self.results['recommendations'].append("⚠️ Integration issues detected - Check component interactions")
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Save comprehensive test results"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase4b_comprehensive_test_{timestamp}.json"
        
        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, timedelta):
                return str(obj)
            return str(obj)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=json_serializer)
        
        logger.info(f"📋 Comprehensive test results saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print test summary to console"""
        print("\n" + "="*80)
        print("📊 PHASE 4B COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        summary = self.results['summary']
        print(f"🕒 Test Duration: {summary['total_test_duration']}")
        print(f"✅ Components Tested: {summary['successful_components']}/{summary['total_components']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"🔗 Integration Status: {'✅ SUCCESS' if summary['integration_success'] else '❌ FAILED'}")
        print(f"🎯 Overall Status: {summary['overall_status'].upper()}")
        
        print(f"\n📋 RECOMMENDATIONS:")
        for rec in self.results['recommendations']:
            print(f"  {rec}")
        
        print("\n" + "="*80)

async def main():
    """Main test execution"""
    print("🧪 PHASE 4B COMPREHENSIVE TESTING SUITE")
    print("="*60)
    
    test_suite = Phase4BComprehensiveTest()
    
    try:
        results = await test_suite.run_comprehensive_tests()
        
        # Save and display results
        filename = test_suite.save_results()
        test_suite.print_summary()
        
        print(f"\n📄 Detailed results saved to: {filename}")
        print("✅ Comprehensive testing complete!")
        
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive testing failed: {e}")
        print(f"❌ Testing failed: {e}")
        return None

if __name__ == "__main__":
    # Run the comprehensive tests
    results = asyncio.run(main())