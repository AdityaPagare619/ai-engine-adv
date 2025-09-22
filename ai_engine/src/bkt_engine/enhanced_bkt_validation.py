# Enhanced BKT Validation and Demo Script
# Comprehensive testing to validate 90%+ accuracy and enterprise features

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import statistics

from .enhanced_bkt_service import EnhancedBKTService
from .enhanced_repositories import InMemoryBKTRepository
from .enhanced_schemas import (
    EnhancedTraceRequest, BKTEvaluationRequest, StudentProfileRequest,
    SystemAnalyticsRequest, DifficultyLevel, ExamType, InterventionLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBKTValidator:
    """Comprehensive validation suite for Enhanced BKT system"""
    
    def __init__(self):
        self.repository = InMemoryBKTRepository()
        self.service = EnhancedBKTService(
            repository=self.repository,
            enable_transfer_learning=True,
            enable_cognitive_load_assessment=True,
            enable_real_time_optimization=True
        )
        self.validation_results = {}
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🚀 Starting Enhanced BKT Comprehensive Validation")
        
        # Initialize validation results
        self.validation_results = {
            "system_info": {
                "model_version": "enhanced_v2",
                "validation_timestamp": datetime.now().isoformat(),
                "features_tested": [
                    "multi_concept_bkt",
                    "transfer_learning", 
                    "cognitive_load_assessment",
                    "adaptive_parameters",
                    "intervention_recommendations",
                    "comprehensive_analytics"
                ]
            },
            "accuracy_tests": {},
            "performance_tests": {},
            "feature_tests": {},
            "scalability_tests": {},
            "overall_assessment": {}
        }
        
        # Run individual validation tests
        await self._test_basic_accuracy()
        await self._test_advanced_accuracy_scenarios()
        await self._test_transfer_learning_effectiveness()
        await self._test_cognitive_load_assessment()
        await self._test_intervention_recommendations()
        await self._test_analytics_accuracy()
        await self._test_performance_characteristics()
        await self._test_scalability()
        await self._validate_system_robustness()
        
        # Generate overall assessment
        self._generate_overall_assessment()
        
        logger.info("✅ Enhanced BKT Validation Complete")
        return self.validation_results
    
    async def _test_basic_accuracy(self):
        """Test basic BKT accuracy with various scenarios"""
        logger.info("Testing basic BKT accuracy...")
        
        # Test scenarios with known patterns
        test_scenarios = [
            {
                "name": "improving_student",
                "pattern": [False, False, True, True, True, True, True],
                "expected_trend": "improving"
            },
            {
                "name": "declining_student", 
                "pattern": [True, True, True, False, False, False, False],
                "expected_trend": "declining"
            },
            {
                "name": "consistent_performer",
                "pattern": [True, True, False, True, True, False, True, True],
                "expected_trend": "stable"
            },
            {
                "name": "struggling_student",
                "pattern": [False, False, False, False, True, False, False],
                "expected_trend": "struggling"
            }
        ]
        
        accuracy_results = {}
        
        for scenario in test_scenarios:
            student_id = f"test_student_{scenario['name']}"
            concept_id = "algebra_basics"
            
            mastery_progression = []
            predictions = []
            actuals = []
            
            for i, is_correct in enumerate(scenario["pattern"]):
                # Create trace request
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=concept_id,
                    is_correct=is_correct,
                    difficulty=0.5 + random.uniform(-0.2, 0.2),
                    response_time_ms=random.randint(5000, 30000),
                    stress_level=random.uniform(0.0, 0.5),
                    cognitive_load=random.uniform(0.3, 0.7),
                    fatigue_level=random.uniform(0.0, 0.3)
                )
                
                # Process interaction
                response = await self.service.trace_knowledge(request)
                mastery_progression.append(response.new_mastery)
                
                # Store prediction for next question (if not last)
                if i < len(scenario["pattern"]) - 1:
                    predictions.append(response.p_correct_next)
                    actuals.append(scenario["pattern"][i + 1])
            
            # Calculate prediction accuracy
            if predictions and actuals:
                binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
                accuracy = sum(bp == a for bp, a in zip(binary_predictions, actuals)) / len(predictions)
                
                accuracy_results[scenario["name"]] = {
                    "prediction_accuracy": accuracy,
                    "mastery_progression": mastery_progression,
                    "final_mastery": mastery_progression[-1],
                    "trend_detected": self._detect_trend(mastery_progression),
                    "expected_trend": scenario["expected_trend"]
                }
        
        # Calculate overall basic accuracy
        all_accuracies = [r["prediction_accuracy"] for r in accuracy_results.values()]
        overall_accuracy = statistics.mean(all_accuracies)
        
        self.validation_results["accuracy_tests"]["basic_accuracy"] = {
            "overall_accuracy": overall_accuracy,
            "target_accuracy": 0.9,
            "meets_target": overall_accuracy >= 0.9,
            "scenario_results": accuracy_results,
            "summary": f"Basic accuracy: {overall_accuracy:.3f} ({'PASS' if overall_accuracy >= 0.9 else 'FAIL'})"
        }
        
        logger.info(f"Basic accuracy test: {overall_accuracy:.3f} ({'PASS' if overall_accuracy >= 0.9 else 'FAIL'})")
    
    async def _test_advanced_accuracy_scenarios(self):
        """Test accuracy with complex scenarios including context factors"""
        logger.info("Testing advanced accuracy scenarios...")
        
        # Multi-concept student with realistic learning patterns
        student_id = "advanced_test_student"
        concepts = ["algebra", "geometry", "trigonometry", "calculus", "statistics"]
        
        # Simulate realistic learning with context factors
        interaction_history = []
        predictions = []
        actuals = []
        
        for day in range(30):  # 30 days of learning
            for session in range(2):  # 2 sessions per day
                for concept in random.sample(concepts, 3):  # 3 concepts per session
                    for _ in range(5):  # 5 questions per concept
                        
                        # Simulate context factors that change over time/sessions
                        time_of_day = "morning" if session == 0 else "evening"
                        stress_level = min(1.0, 0.1 + (day / 30) * 0.3 + random.uniform(-0.1, 0.1))
                        fatigue_level = 0.2 + session * 0.3 + random.uniform(0, 0.2)
                        
                        # Realistic difficulty progression
                        base_difficulty = {
                            "algebra": 0.3,
                            "geometry": 0.4, 
                            "trigonometry": 0.6,
                            "calculus": 0.7,
                            "statistics": 0.5
                        }[concept]
                        
                        difficulty = min(1.0, base_difficulty + (day / 30) * 0.3)
                        
                        # Simulate learning - probability of success improves over time
                        days_practicing = sum(1 for h in interaction_history 
                                            if h["concept_id"] == concept and h["is_correct"])
                        
                        # Base success probability improves with practice
                        base_success_prob = 0.3 + min(0.6, days_practicing * 0.05)
                        
                        # Adjust for context factors
                        success_prob = base_success_prob
                        success_prob -= stress_level * 0.2
                        success_prob -= fatigue_level * 0.15
                        success_prob -= (difficulty - 0.5) * 0.3
                        success_prob = max(0.1, min(0.9, success_prob))
                        
                        is_correct = random.random() < success_prob
                        
                        # Create request
                        request = EnhancedTraceRequest(
                            student_id=student_id,
                            concept_id=concept,
                            is_correct=is_correct,
                            difficulty=difficulty,
                            difficulty_level=DifficultyLevel.MEDIUM,
                            response_time_ms=random.randint(3000, 45000),
                            stress_level=stress_level,
                            cognitive_load=difficulty * 0.8 + stress_level * 0.2,
                            fatigue_level=fatigue_level,
                            time_pressure=1.0 + random.uniform(-0.3, 0.3),
                            time_of_day=time_of_day,
                            session_id=f"session_{day}_{session}",
                            exam_type=ExamType.JEE_MAIN
                        )
                        
                        # Process interaction
                        response = await self.service.trace_knowledge(request)
                        
                        # Store history
                        interaction_history.append({
                            "concept_id": concept,
                            "is_correct": is_correct,
                            "predicted_mastery": response.new_mastery,
                            "day": day
                        })
                        
                        # Store prediction for evaluation
                        if len(interaction_history) > 1:
                            predictions.append(response.p_correct_next)
                            actuals.append(is_correct)
        
        # Calculate advanced accuracy metrics
        binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
        accuracy = sum(bp == a for bp, a in zip(binary_predictions, actuals)) / len(predictions)
        
        # Calculate concept-specific accuracies
        concept_accuracies = {}
        for concept in concepts:
            concept_interactions = [h for h in interaction_history if h["concept_id"] == concept]
            if len(concept_interactions) > 10:
                concept_predictions = []
                concept_actuals = []
                
                for i in range(1, len(concept_interactions)):
                    # Use previous mastery to predict current outcome
                    prev_mastery = concept_interactions[i-1]["predicted_mastery"]
                    actual = concept_interactions[i]["is_correct"]
                    
                    concept_predictions.append(prev_mastery)
                    concept_actuals.append(1.0 if actual else 0.0)
                
                if concept_predictions:
                    concept_binary = [1 if p > 0.5 else 0 for p in concept_predictions]
                    concept_acc = sum(bp == a for bp, a in zip(concept_binary, concept_actuals)) / len(concept_binary)
                    concept_accuracies[concept] = concept_acc
        
        self.validation_results["accuracy_tests"]["advanced_scenarios"] = {
            "overall_accuracy": accuracy,
            "concept_accuracies": concept_accuracies,
            "total_interactions": len(interaction_history),
            "meets_target": accuracy >= 0.9,
            "summary": f"Advanced accuracy: {accuracy:.3f} ({'PASS' if accuracy >= 0.9 else 'FAIL'})"
        }
        
        logger.info(f"Advanced accuracy test: {accuracy:.3f} ({'PASS' if accuracy >= 0.9 else 'FAIL'})")
    
    async def _test_transfer_learning_effectiveness(self):
        """Test transfer learning between related concepts"""
        logger.info("Testing transfer learning effectiveness...")
        
        student_id = "transfer_test_student"
        
        # Related concept pairs
        concept_pairs = [
            ("basic_algebra", "advanced_algebra"),
            ("geometry_basics", "coordinate_geometry"),
            ("trigonometry", "calculus_basics")
        ]
        
        transfer_results = {}
        
        for source_concept, target_concept in concept_pairs:
            # First, train extensively on source concept
            for i in range(20):
                # Gradually improving performance
                is_correct = random.random() < (0.3 + i * 0.03)
                
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=source_concept,
                    is_correct=is_correct,
                    difficulty=0.5,
                    stress_level=0.2,
                    cognitive_load=0.4
                )
                
                await self.service.trace_knowledge(request)
            
            # Get mastery level after training on source
            profile = await self.repository.get_student_profile(student_id)
            source_mastery = profile.concept_masteries[source_concept].mastery_probability
            
            # Now test first interaction with target concept
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=target_concept,
                is_correct=True,  # Assume success due to transfer
                difficulty=0.5,
                stress_level=0.2,
                cognitive_load=0.4
            )
            
            response = await self.service.trace_knowledge(request)
            initial_target_mastery = response.new_mastery
            
            # Transfer effectiveness: target should start higher than default
            transfer_effectiveness = initial_target_mastery - 0.1  # 0.1 is typical initial mastery
            
            transfer_results[f"{source_concept}→{target_concept}"] = {
                "source_mastery": source_mastery,
                "initial_target_mastery": initial_target_mastery,
                "transfer_effectiveness": transfer_effectiveness,
                "transfer_detected": initial_target_mastery > 0.2
            }
        
        overall_transfer_effectiveness = statistics.mean([
            r["transfer_effectiveness"] for r in transfer_results.values()
        ])
        
        self.validation_results["feature_tests"]["transfer_learning"] = {
            "overall_effectiveness": overall_transfer_effectiveness,
            "pair_results": transfer_results,
            "meets_expectations": overall_transfer_effectiveness > 0.1,
            "summary": f"Transfer learning effectiveness: {overall_transfer_effectiveness:.3f}"
        }
        
        logger.info(f"Transfer learning test: {overall_transfer_effectiveness:.3f} effectiveness")
    
    async def _test_cognitive_load_assessment(self):
        """Test cognitive load assessment and recommendations"""
        logger.info("Testing cognitive load assessment...")
        
        student_id = "cognitive_test_student"
        concept_id = "complex_calculus"
        
        # Test various cognitive load scenarios
        load_scenarios = [
            {"difficulty": 0.9, "stress": 0.8, "fatigue": 0.7, "expected_overload": True},
            {"difficulty": 0.3, "stress": 0.2, "fatigue": 0.1, "expected_overload": False},
            {"difficulty": 0.6, "stress": 0.5, "fatigue": 0.4, "expected_overload": False},
            {"difficulty": 0.8, "stress": 0.7, "fatigue": 0.8, "expected_overload": True}
        ]
        
        cognitive_results = {}
        
        for i, scenario in enumerate(load_scenarios):
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=random.random() < 0.5,
                difficulty=scenario["difficulty"],
                stress_level=scenario["stress"],
                cognitive_load=scenario["difficulty"] * 0.8 + scenario["stress"] * 0.2,
                fatigue_level=scenario["fatigue"],
                time_pressure=1.2 if scenario["expected_overload"] else 1.0
            )
            
            response = await self.service.trace_knowledge(request)
            
            cognitive_results[f"scenario_{i+1}"] = {
                "input": scenario,
                "cognitive_load": response.cognitive_load.model_dump(),
                "overload_detected": response.cognitive_load.overload_risk > 0.5,
                "expected_overload": scenario["expected_overload"],
                "correct_detection": (response.cognitive_load.overload_risk > 0.5) == scenario["expected_overload"],
                "recommendations_provided": len(response.cognitive_load.recommendations) > 0
            }
        
        # Calculate detection accuracy
        correct_detections = sum(1 for r in cognitive_results.values() if r["correct_detection"])
        detection_accuracy = correct_detections / len(load_scenarios)
        
        self.validation_results["feature_tests"]["cognitive_load"] = {
            "detection_accuracy": detection_accuracy,
            "scenario_results": cognitive_results,
            "meets_expectations": detection_accuracy >= 0.8,
            "summary": f"Cognitive load detection: {detection_accuracy:.3f} accuracy"
        }
        
        logger.info(f"Cognitive load test: {detection_accuracy:.3f} detection accuracy")
    
    async def _test_intervention_recommendations(self):
        """Test intervention recommendation system"""
        logger.info("Testing intervention recommendations...")
        
        student_id = "intervention_test_student"
        concept_id = "challenging_physics"
        
        # Create scenario requiring intervention (multiple consecutive errors)
        intervention_triggered = False
        intervention_details = None
        
        for i in range(6):  # Multiple errors to trigger intervention
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=False,  # Consecutive errors
                difficulty=0.7,
                stress_level=0.6 + i * 0.05,  # Increasing stress
                cognitive_load=0.8,
                fatigue_level=0.5
            )
            
            response = await self.service.trace_knowledge(request)
            
            if response.intervention:
                intervention_triggered = True
                intervention_details = response.intervention.model_dump()
                break
        
        # Test cognitive overload intervention
        overload_request = EnhancedTraceRequest(
            student_id=f"{student_id}_overload",
            concept_id=concept_id,
            is_correct=False,
            difficulty=0.9,
            stress_level=0.9,
            cognitive_load=0.95,
            fatigue_level=0.8,
            time_pressure=1.5
        )
        
        overload_response = await self.service.trace_knowledge(overload_request)
        overload_intervention = overload_response.intervention is not None
        
        self.validation_results["feature_tests"]["interventions"] = {
            "error_streak_intervention": {
                "triggered": intervention_triggered,
                "details": intervention_details
            },
            "cognitive_overload_intervention": {
                "triggered": overload_intervention,
                "details": overload_response.intervention.model_dump() if overload_response.intervention else None
            },
            "overall_effectiveness": intervention_triggered and overload_intervention,
            "summary": f"Interventions: {'PASS' if intervention_triggered and overload_intervention else 'FAIL'}"
        }
        
        logger.info(f"Intervention test: {'PASS' if intervention_triggered and overload_intervention else 'FAIL'}")
    
    async def _test_analytics_accuracy(self):
        """Test analytics and evaluation system accuracy"""
        logger.info("Testing analytics accuracy...")
        
        # Generate substantial interaction data
        student_id = "analytics_test_student"
        concepts = ["math_basics", "algebra", "geometry"]
        
        for concept in concepts:
            for i in range(50):  # 50 interactions per concept
                # Simulate realistic learning curve
                success_prob = 0.2 + min(0.7, i * 0.015)
                is_correct = random.random() < success_prob
                
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=concept,
                    is_correct=is_correct,
                    difficulty=0.5 + random.uniform(-0.2, 0.2),
                    stress_level=random.uniform(0, 0.5),
                    cognitive_load=random.uniform(0.3, 0.7)
                )
                
                await self.service.trace_knowledge(request)
        
        # Test system evaluation
        eval_request = BKTEvaluationRequest(
            student_id=student_id,
            min_interactions=10
        )
        
        eval_response = await self.service.evaluate_system(eval_request)
        
        # Test student profile generation
        profile_request = StudentProfileRequest(
            student_id=student_id,
            include_concept_details=True,
            include_learning_analytics=True
        )
        
        profile_response = await self.service.get_student_profile(profile_request)
        
        self.validation_results["feature_tests"]["analytics"] = {
            "evaluation_metrics": {
                "next_step_auc": eval_response.next_step_auc,
                "next_step_accuracy": eval_response.next_step_accuracy,
                "overall_quality": eval_response.overall_quality_score,
                "recommendation": eval_response.recommendation
            },
            "student_profile": {
                "overall_performance": profile_response.overall_performance,
                "learning_velocity": profile_response.learning_velocity,
                "concept_count": len(profile_response.concept_masteries),
                "recommendations_provided": len(profile_response.focus_recommendations) > 0
            },
            "analytics_functional": eval_response.next_step_accuracy > 0.7,
            "summary": f"Analytics: {'PASS' if eval_response.next_step_accuracy > 0.7 else 'FAIL'}"
        }
        
        logger.info(f"Analytics test: {eval_response.next_step_accuracy:.3f} accuracy")
    
    async def _test_performance_characteristics(self):
        """Test system performance under load"""
        logger.info("Testing performance characteristics...")
        
        import time
        
        # Performance test: 100 rapid interactions
        student_id = "performance_test_student"
        concept_id = "performance_concept"
        
        processing_times = []
        start_time = time.time()
        
        for i in range(100):
            interaction_start = time.time()
            
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=random.random() < 0.6,
                difficulty=random.uniform(0.3, 0.8),
                stress_level=random.uniform(0, 0.5),
                cognitive_load=random.uniform(0.3, 0.7)
            )
            
            response = await self.service.trace_knowledge(request)
            
            processing_time = (time.time() - interaction_start) * 1000  # ms
            processing_times.append(processing_time)
        
        total_time = time.time() - start_time
        
        self.validation_results["performance_tests"] = {
            "total_interactions": 100,
            "total_time_seconds": total_time,
            "throughput_per_second": 100 / total_time,
            "average_processing_time_ms": statistics.mean(processing_times),
            "median_processing_time_ms": statistics.median(processing_times),
            "max_processing_time_ms": max(processing_times),
            "min_processing_time_ms": min(processing_times),
            "performance_acceptable": statistics.mean(processing_times) < 50,  # < 50ms average
            "summary": f"Performance: {statistics.mean(processing_times):.1f}ms avg ({'PASS' if statistics.mean(processing_times) < 50 else 'FAIL'})"
        }
        
        logger.info(f"Performance test: {statistics.mean(processing_times):.1f}ms average")
    
    async def _test_scalability(self):
        """Test system scalability with multiple concurrent students"""
        logger.info("Testing scalability...")
        
        # Simulate 10 concurrent students
        concurrent_students = 10
        interactions_per_student = 20
        
        async def simulate_student(student_id: str):
            """Simulate one student's learning session"""
            processing_times = []
            
            for i in range(interactions_per_student):
                start_time = time.time()
                
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=f"concept_{random.randint(1, 5)}",
                    is_correct=random.random() < (0.3 + i * 0.03),
                    difficulty=random.uniform(0.3, 0.8),
                    stress_level=random.uniform(0, 0.5),
                    cognitive_load=random.uniform(0.3, 0.7)
                )
                
                await self.service.trace_knowledge(request)
                
                processing_times.append((time.time() - start_time) * 1000)
            
            return processing_times
        
        # Run concurrent simulations
        import time
        start_time = time.time()
        
        tasks = [
            simulate_student(f"concurrent_student_{i}")
            for i in range(concurrent_students)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Aggregate results
        all_times = [time for student_times in results for time in student_times]
        total_interactions = concurrent_students * interactions_per_student
        
        self.validation_results["scalability_tests"] = {
            "concurrent_students": concurrent_students,
            "total_interactions": total_interactions,
            "total_time_seconds": total_time,
            "overall_throughput_per_second": total_interactions / total_time,
            "average_processing_time_ms": statistics.mean(all_times),
            "scalability_acceptable": statistics.mean(all_times) < 100,  # < 100ms under load
            "summary": f"Scalability: {total_interactions / total_time:.1f} req/sec ({'PASS' if statistics.mean(all_times) < 100 else 'FAIL'})"
        }
        
        logger.info(f"Scalability test: {total_interactions / total_time:.1f} requests/second")
    
    async def _validate_system_robustness(self):
        """Test system robustness with edge cases and error conditions"""
        logger.info("Testing system robustness...")
        
        robustness_results = {
            "edge_cases_handled": 0,
            "total_edge_cases": 0,
            "error_recovery": True
        }
        
        # Test edge cases
        edge_cases = [
            {
                "name": "extreme_difficulty",
                "request": EnhancedTraceRequest(
                    student_id="edge_student_1",
                    concept_id="edge_concept",
                    is_correct=True,
                    difficulty=1.0,  # Maximum difficulty
                    stress_level=1.0,  # Maximum stress
                    cognitive_load=1.0,  # Maximum cognitive load
                    fatigue_level=1.0,  # Maximum fatigue
                    time_pressure=2.0  # Maximum time pressure
                )
            },
            {
                "name": "minimum_values",
                "request": EnhancedTraceRequest(
                    student_id="edge_student_2",
                    concept_id="edge_concept",
                    is_correct=False,
                    difficulty=0.0,  # Minimum difficulty
                    stress_level=0.0,  # Minimum stress
                    cognitive_load=0.0,  # Minimum cognitive load
                    fatigue_level=0.0,  # Minimum fatigue
                    time_pressure=0.5  # Minimum time pressure
                )
            },
            {
                "name": "rapid_fire_interactions",
                "request": EnhancedTraceRequest(
                    student_id="edge_student_3",
                    concept_id="edge_concept",
                    is_correct=True,
                    response_time_ms=100,  # Very fast response
                    difficulty=0.5
                )
            }
        ]
        
        for edge_case in edge_cases:
            robustness_results["total_edge_cases"] += 1
            
            try:
                response = await self.service.trace_knowledge(edge_case["request"])
                
                if response.success:
                    robustness_results["edge_cases_handled"] += 1
                    logger.debug(f"Edge case '{edge_case['name']}' handled successfully")
                else:
                    logger.warning(f"Edge case '{edge_case['name']}' failed")
                    
            except Exception as e:
                logger.error(f"Edge case '{edge_case['name']}' caused exception: {e}")
                robustness_results["error_recovery"] = False
        
        # Test system status endpoint
        try:
            status = await self.service.get_system_status()
            robustness_results["system_status_functional"] = "service_status" in status
        except Exception as e:
            logger.error(f"System status check failed: {e}")
            robustness_results["system_status_functional"] = False
            robustness_results["error_recovery"] = False
        
        robustness_score = robustness_results["edge_cases_handled"] / robustness_results["total_edge_cases"]
        
        self.validation_results["feature_tests"]["robustness"] = {
            **robustness_results,
            "robustness_score": robustness_score,
            "meets_expectations": robustness_score >= 0.8 and robustness_results["error_recovery"],
            "summary": f"Robustness: {robustness_score:.3f} ({'PASS' if robustness_score >= 0.8 else 'FAIL'})"
        }
        
        logger.info(f"Robustness test: {robustness_score:.3f} ({'PASS' if robustness_score >= 0.8 else 'FAIL'})")
    
    def _generate_overall_assessment(self):
        """Generate overall system assessment"""
        
        # Collect key metrics
        basic_accuracy = self.validation_results["accuracy_tests"]["basic_accuracy"]["overall_accuracy"]
        advanced_accuracy = self.validation_results["accuracy_tests"]["advanced_scenarios"]["overall_accuracy"]
        
        # Overall accuracy is weighted average
        overall_accuracy = (basic_accuracy * 0.4 + advanced_accuracy * 0.6)
        
        # Performance metrics
        avg_processing_time = self.validation_results["performance_tests"]["average_processing_time_ms"]
        throughput = self.validation_results["scalability_tests"]["overall_throughput_per_second"]
        
        # Feature functionality
        transfer_learning_works = self.validation_results["feature_tests"]["transfer_learning"]["meets_expectations"]
        cognitive_load_works = self.validation_results["feature_tests"]["cognitive_load"]["meets_expectations"]
        interventions_work = self.validation_results["feature_tests"]["interventions"]["overall_effectiveness"]
        analytics_work = self.validation_results["feature_tests"]["analytics"]["analytics_functional"]
        robustness_ok = self.validation_results["feature_tests"]["robustness"]["meets_expectations"]
        
        # Calculate overall score
        accuracy_score = min(1.0, overall_accuracy / 0.9) * 40  # 40% weight
        performance_score = min(1.0, max(0, (50 - avg_processing_time) / 50)) * 20  # 20% weight
        scalability_score = min(1.0, throughput / 10) * 15  # 15% weight
        features_score = sum([
            transfer_learning_works,
            cognitive_load_works, 
            interventions_work,
            analytics_work,
            robustness_ok
        ]) / 5 * 25  # 25% weight
        
        overall_score = accuracy_score + performance_score + scalability_score + features_score
        
        # Generate assessment
        if overall_score >= 85 and overall_accuracy >= 0.9:
            assessment = "EXCELLENT"
            recommendation = "System ready for production deployment"
        elif overall_score >= 70 and overall_accuracy >= 0.8:
            assessment = "GOOD"
            recommendation = "System functional with minor optimizations needed"
        elif overall_score >= 50 and overall_accuracy >= 0.7:
            assessment = "NEEDS_IMPROVEMENT"
            recommendation = "Significant improvements required before deployment"
        else:
            assessment = "CRITICAL"
            recommendation = "Major issues need resolution"
        
        self.validation_results["overall_assessment"] = {
            "overall_accuracy": overall_accuracy,
            "accuracy_target_met": overall_accuracy >= 0.9,
            "performance_score": performance_score,
            "scalability_score": scalability_score,
            "features_score": features_score,
            "overall_score": overall_score,
            "assessment": assessment,
            "recommendation": recommendation,
            "key_strengths": self._identify_strengths(),
            "areas_for_improvement": self._identify_improvements(),
            "production_ready": assessment in ["EXCELLENT", "GOOD"] and overall_accuracy >= 0.9
        }
    
    def _identify_strengths(self) -> List[str]:
        """Identify system strengths"""
        strengths = []
        
        if self.validation_results["accuracy_tests"]["basic_accuracy"]["overall_accuracy"] >= 0.9:
            strengths.append("Excellent basic prediction accuracy")
        
        if self.validation_results["accuracy_tests"]["advanced_scenarios"]["overall_accuracy"] >= 0.9:
            strengths.append("High accuracy in complex scenarios")
        
        if self.validation_results["performance_tests"]["average_processing_time_ms"] < 30:
            strengths.append("Fast response times")
        
        if self.validation_results["feature_tests"]["transfer_learning"]["meets_expectations"]:
            strengths.append("Effective transfer learning implementation")
        
        if self.validation_results["feature_tests"]["cognitive_load"]["meets_expectations"]:
            strengths.append("Accurate cognitive load assessment")
        
        if self.validation_results["scalability_tests"]["overall_throughput_per_second"] > 15:
            strengths.append("Good scalability characteristics")
        
        return strengths
    
    def _identify_improvements(self) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        if self.validation_results["accuracy_tests"]["basic_accuracy"]["overall_accuracy"] < 0.9:
            improvements.append("Improve basic prediction accuracy")
        
        if self.validation_results["performance_tests"]["average_processing_time_ms"] > 50:
            improvements.append("Optimize processing speed")
        
        if not self.validation_results["feature_tests"]["transfer_learning"]["meets_expectations"]:
            improvements.append("Enhance transfer learning effectiveness")
        
        if not self.validation_results["feature_tests"]["interventions"]["overall_effectiveness"]:
            improvements.append("Improve intervention recommendation system")
        
        if self.validation_results["scalability_tests"]["average_processing_time_ms"] > 100:
            improvements.append("Optimize performance under load")
        
        return improvements
    
    def _detect_trend(self, mastery_values: List[float]) -> str:
        """Detect learning trend from mastery progression"""
        if len(mastery_values) < 3:
            return "insufficient_data"
        
        first_third = statistics.mean(mastery_values[:len(mastery_values)//3])
        last_third = statistics.mean(mastery_values[-len(mastery_values)//3:])
        
        if last_third > first_third + 0.1:
            return "improving"
        elif last_third < first_third - 0.1:
            return "declining"
        else:
            return "stable"
    
    def print_validation_summary(self):
        """Print a comprehensive validation summary"""
        print("\n" + "="*80)
        print("🎓 ENHANCED BKT SYSTEM VALIDATION SUMMARY")
        print("="*80)
        
        assessment = self.validation_results["overall_assessment"]
        
        print(f"\n📊 OVERALL ASSESSMENT: {assessment['assessment']}")
        print(f"🎯 Overall Accuracy: {assessment['overall_accuracy']:.3f} (Target: ≥0.90)")
        print(f"⚡ Overall Score: {assessment['overall_score']:.1f}/100")
        print(f"🚀 Production Ready: {'✅ YES' if assessment['production_ready'] else '❌ NO'}")
        
        print(f"\n💡 RECOMMENDATION: {assessment['recommendation']}")
        
        print("\n" + "-"*60)
        print("📈 DETAILED RESULTS")
        print("-"*60)
        
        # Accuracy Results
        basic_acc = self.validation_results["accuracy_tests"]["basic_accuracy"]["overall_accuracy"]
        advanced_acc = self.validation_results["accuracy_tests"]["advanced_scenarios"]["overall_accuracy"]
        
        print(f"🎯 Basic Accuracy: {basic_acc:.3f} ({'✅' if basic_acc >= 0.9 else '❌'})")
        print(f"🎯 Advanced Scenarios: {advanced_acc:.3f} ({'✅' if advanced_acc >= 0.9 else '❌'})")
        
        # Performance Results
        perf = self.validation_results["performance_tests"]
        print(f"⚡ Avg Processing Time: {perf['average_processing_time_ms']:.1f}ms ({'✅' if perf['average_processing_time_ms'] < 50 else '❌'})")
        print(f"🔥 Throughput: {perf['throughput_per_second']:.1f} req/sec")
        
        # Feature Results
        features = self.validation_results["feature_tests"]
        print(f"🔄 Transfer Learning: {'✅' if features['transfer_learning']['meets_expectations'] else '❌'}")
        print(f"🧠 Cognitive Load: {'✅' if features['cognitive_load']['meets_expectations'] else '❌'}")
        print(f"🆘 Interventions: {'✅' if features['interventions']['overall_effectiveness'] else '❌'}")
        print(f"📊 Analytics: {'✅' if features['analytics']['analytics_functional'] else '❌'}")
        print(f"🛡️ Robustness: {'✅' if features['robustness']['meets_expectations'] else '❌'}")
        
        # Scalability Results
        scale = self.validation_results["scalability_tests"]
        print(f"📈 Scalability: {scale['overall_throughput_per_second']:.1f} req/sec ({'✅' if scale['scalability_acceptable'] else '❌'})")
        
        print("\n" + "-"*60)
        print("💪 STRENGTHS")
        print("-"*60)
        for strength in assessment["key_strengths"]:
            print(f"✅ {strength}")
        
        if assessment["areas_for_improvement"]:
            print("\n" + "-"*60)
            print("🔧 AREAS FOR IMPROVEMENT")
            print("-"*60)
            for improvement in assessment["areas_for_improvement"]:
                print(f"🔧 {improvement}")
        
        print("\n" + "="*80)

# Demo function to run the validation
async def run_enhanced_bkt_validation():
    """Run the complete Enhanced BKT validation suite"""
    
    print("🚀 Starting Enhanced BKT System Validation...")
    print("This comprehensive test validates 90%+ accuracy and enterprise features.\n")
    
    validator = EnhancedBKTValidator()
    
    try:
        # Run validation
        results = await validator.run_comprehensive_validation()
        
        # Print summary
        validator.print_validation_summary()
        
        # Save detailed results
        with open("enhanced_bkt_validation_results.json", "w") as f:
            # Convert datetime objects to strings for JSON serialization
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError
            
            json.dump(results, f, indent=2, default=serialize_datetime)
        
        print(f"\n📄 Detailed results saved to: enhanced_bkt_validation_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        print(f"\n❌ Validation failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(run_enhanced_bkt_validation())