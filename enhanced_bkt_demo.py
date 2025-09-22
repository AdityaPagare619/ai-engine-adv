#!/usr/bin/env python3
"""
Enhanced BKT System Demo
========================

A comprehensive demonstration of the Enhanced Bayesian Knowledge Tracing (BKT) system
designed to achieve 90%+ accuracy in educational AI applications.

This demo showcases:
- Multi-concept knowledge tracing with adaptive parameters
- Transfer learning between related concepts
- Cognitive load assessment and management
- Real-time intervention recommendations
- Advanced analytics and student profiling
- Performance validation and system health monitoring

Usage:
    python enhanced_bkt_demo.py

Requirements:
    - Python 3.8+
    - pydantic
    - asyncio
    - Standard Python libraries (datetime, json, logging, etc.)
"""

import sys
import os
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the AI engine source path to Python path
current_dir = Path(__file__).parent
ai_engine_path = current_dir / "ai_engine" / "src"
sys.path.insert(0, str(ai_engine_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_bkt_demo.log')
    ]
)
logger = logging.getLogger(__name__)

# Import Enhanced BKT components
try:
    from bkt_engine import (
        EnhancedBKTService, 
        EnhancedTraceRequest,
        EnhancedTraceResponse,
        BKTEvaluationRequest,
        StudentProfileRequest,
        SystemAnalyticsRequest,
        ExamType,
        DifficultyLevel,
        InterventionLevel
    )
    logger.info("✅ Successfully imported Enhanced BKT components")
except ImportError as e:
    logger.error(f"❌ Failed to import Enhanced BKT components: {e}")
    print(f"Error: Could not import Enhanced BKT components. Please ensure the ai_engine module is properly installed.")
    print(f"Import error: {e}")
    sys.exit(1)

class EnhancedBKTDemo:
    """Comprehensive demonstration of Enhanced BKT system capabilities"""
    
    def __init__(self):
        """Initialize the demo with Enhanced BKT service"""
        self.bkt_service = EnhancedBKTService(
            enable_transfer_learning=True,
            enable_cognitive_load_assessment=True,
            enable_real_time_optimization=True
        )
        
        # Demo data
        self.demo_students = [
            "alice_johnson", "bob_smith", "carol_davis", 
            "david_wilson", "emma_brown", "frank_miller"
        ]
        
        self.demo_concepts = {
            "basic_algebra": {"difficulty": 0.3, "subject": "mathematics"},
            "quadratic_equations": {"difficulty": 0.6, "subject": "mathematics"},
            "calculus_derivatives": {"difficulty": 0.8, "subject": "mathematics"},
            "organic_chemistry": {"difficulty": 0.7, "subject": "chemistry"},
            "thermodynamics": {"difficulty": 0.75, "subject": "physics"},
            "electric_circuits": {"difficulty": 0.65, "subject": "physics"}
        }
        
        self.demo_results = {}
        
    async def run_comprehensive_demo(self):
        """Run the complete Enhanced BKT demonstration"""
        print("\n" + "="*80)
        print("🎓 ENHANCED BKT SYSTEM DEMONSTRATION")
        print("Enterprise-grade Bayesian Knowledge Tracing with 90%+ Accuracy")
        print("="*80)
        
        logger.info("Starting comprehensive Enhanced BKT demonstration")
        
        # Initialize demo results
        self.demo_results = {
            "demo_info": {
                "timestamp": datetime.now().isoformat(),
                "system_version": "enhanced_v2",
                "students_simulated": len(self.demo_students),
                "concepts_tracked": len(self.demo_concepts)
            },
            "demonstrations": {}
        }
        
        try:
            # 1. Basic Knowledge Tracing Demo
            await self._demo_basic_knowledge_tracing()
            
            # 2. Transfer Learning Demo
            await self._demo_transfer_learning()
            
            # 3. Cognitive Load Assessment Demo
            await self._demo_cognitive_load_assessment()
            
            # 4. Intervention Recommendations Demo
            await self._demo_intervention_system()
            
            # 5. Advanced Analytics Demo
            await self._demo_advanced_analytics()
            
            # 6. Multi-Student Simulation Demo
            await self._demo_multi_student_simulation()
            
            # 7. System Performance Demo
            await self._demo_system_performance()
            
            # 8. Generate final summary
            await self._generate_demo_summary()
            
            print("\n🎉 Enhanced BKT Demo completed successfully!")
            logger.info("Enhanced BKT demonstration completed successfully")
            
        except Exception as e:
            logger.error(f"Demo failed: {str(e)}", exc_info=True)
            print(f"\n❌ Demo failed: {str(e)}")
            
        return self.demo_results
    
    async def _demo_basic_knowledge_tracing(self):
        """Demonstrate basic knowledge tracing capabilities"""
        print("\n" + "─"*60)
        print("📚 1. BASIC KNOWLEDGE TRACING DEMONSTRATION")
        print("─"*60)
        
        student_id = "demo_student_basic"
        concept_id = "basic_algebra"
        
        print(f"Simulating learning progression for student: {student_id}")
        print(f"Concept: {concept_id}")
        
        # Simulate learning progression (improving over time)
        interactions = [
            {"correct": False, "difficulty": 0.3, "note": "Initial struggle"},
            {"correct": False, "difficulty": 0.3, "note": "Still learning"},
            {"correct": True, "difficulty": 0.3, "note": "First success"},
            {"correct": True, "difficulty": 0.4, "note": "Building confidence"},
            {"correct": False, "difficulty": 0.6, "note": "Challenge increases"},
            {"correct": True, "difficulty": 0.5, "note": "Recovery"},
            {"correct": True, "difficulty": 0.6, "note": "Mastering concept"},
            {"correct": True, "difficulty": 0.7, "note": "Advanced proficiency"}
        ]
        
        mastery_progression = []
        
        for i, interaction in enumerate(interactions):
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=interaction["correct"],
                difficulty=interaction["difficulty"],
                response_time_ms=5000 + i * 1000,  # Decreasing response time
                stress_level=max(0, 0.7 - i * 0.1),  # Decreasing stress
                cognitive_load=interaction["difficulty"] * 0.8,
                exam_type=ExamType.JEE_MAIN
            )
            
            response = await self.bkt_service.trace_knowledge(request)
            mastery_progression.append(response.new_mastery)
            
            print(f"  Step {i+1}: {'✅' if interaction['correct'] else '❌'} | "
                  f"Mastery: {response.previous_mastery:.3f} → {response.new_mastery:.3f} | "
                  f"Next P(correct): {response.p_correct_next:.3f} | "
                  f"{interaction['note']}")
        
        print(f"\n📊 Learning Progress Summary:")
        print(f"  • Initial mastery: {mastery_progression[0]:.3f}")
        print(f"  • Final mastery: {mastery_progression[-1]:.3f}")
        print(f"  • Improvement: {mastery_progression[-1] - mastery_progression[0]:.3f}")
        print(f"  • Success rate: {sum(i['correct'] for i in interactions) / len(interactions):.3f}")
        
        self.demo_results["demonstrations"]["basic_tracing"] = {
            "student_id": student_id,
            "concept_id": concept_id,
            "interactions": len(interactions),
            "initial_mastery": mastery_progression[0],
            "final_mastery": mastery_progression[-1],
            "improvement": mastery_progression[-1] - mastery_progression[0],
            "success_rate": sum(i['correct'] for i in interactions) / len(interactions)
        }
    
    async def _demo_transfer_learning(self):
        """Demonstrate transfer learning between concepts"""
        print("\n" + "─"*60)
        print("🔄 2. TRANSFER LEARNING DEMONSTRATION")
        print("─"*60)
        
        student_id = "demo_student_transfer"
        
        # First, master basic algebra
        print("Phase 1: Mastering basic algebra...")
        for i in range(8):
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id="basic_algebra",
                is_correct=True,  # Assuming good performance
                difficulty=0.4,
                stress_level=0.3
            )
            await self.bkt_service.trace_knowledge(request)
        
        # Check mastery level
        profile_request = StudentProfileRequest(student_id=student_id)
        profile = await self.bkt_service.get_student_profile(profile_request)
        basic_algebra_mastery = profile.concept_masteries["basic_algebra"].mastery_probability
        
        print(f"  Basic algebra mastery achieved: {basic_algebra_mastery:.3f}")
        
        # Now try quadratic equations (should benefit from transfer)
        print("\nPhase 2: First attempt at quadratic equations (should benefit from transfer)...")
        
        request = EnhancedTraceRequest(
            student_id=student_id,
            concept_id="quadratic_equations",
            is_correct=True,
            difficulty=0.5,
            stress_level=0.4
        )
        
        response = await self.bkt_service.trace_knowledge(request)
        initial_quadratic_mastery = response.new_mastery
        
        print(f"  Quadratic equations initial mastery: {initial_quadratic_mastery:.3f}")
        print(f"  Transfer benefit: {initial_quadratic_mastery - 0.1:.3f} (compared to typical 0.1 start)")
        
        # Show transfer updates
        if response.transfer_updates:
            print(f"  Transfer learning applied: {len(response.transfer_updates)} concept updates")
            for concept, boost in response.transfer_updates.items():
                print(f"    • {concept}: +{boost:.3f}")
        
        self.demo_results["demonstrations"]["transfer_learning"] = {
            "source_concept": "basic_algebra",
            "source_mastery": basic_algebra_mastery,
            "target_concept": "quadratic_equations",
            "target_initial_mastery": initial_quadratic_mastery,
            "transfer_benefit": initial_quadratic_mastery - 0.1,
            "transfer_detected": initial_quadratic_mastery > 0.2
        }
    
    async def _demo_cognitive_load_assessment(self):
        """Demonstrate cognitive load assessment"""
        print("\n" + "─"*60)
        print("🧠 3. COGNITIVE LOAD ASSESSMENT DEMONSTRATION")
        print("─"*60)
        
        student_id = "demo_student_cognitive"
        concept_id = "calculus_derivatives"
        
        # Test different cognitive load scenarios
        scenarios = [
            {
                "name": "Low Load",
                "difficulty": 0.3,
                "stress": 0.2,
                "fatigue": 0.1,
                "time_pressure": 0.8
            },
            {
                "name": "Moderate Load",
                "difficulty": 0.6,
                "stress": 0.5,
                "fatigue": 0.4,
                "time_pressure": 1.0
            },
            {
                "name": "High Load",
                "difficulty": 0.9,
                "stress": 0.8,
                "fatigue": 0.7,
                "time_pressure": 1.4
            },
            {
                "name": "Overload Risk",
                "difficulty": 0.95,
                "stress": 0.9,
                "fatigue": 0.8,
                "time_pressure": 1.6
            }
        ]
        
        cognitive_results = []
        
        for scenario in scenarios:
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=True,  # Focus on load assessment
                difficulty=scenario["difficulty"],
                stress_level=scenario["stress"],
                cognitive_load=scenario["difficulty"] * 0.8 + scenario["stress"] * 0.2,
                fatigue_level=scenario["fatigue"],
                time_pressure=scenario["time_pressure"]
            )
            
            response = await self.bkt_service.trace_knowledge(request)
            cognitive_load = response.cognitive_load
            
            print(f"\n{scenario['name']} Scenario:")
            print(f"  • Total Load: {cognitive_load.total_load:.3f}")
            print(f"  • Intrinsic: {cognitive_load.intrinsic_load:.3f} | "
                  f"Extraneous: {cognitive_load.extraneous_load:.3f} | "
                  f"Germane: {cognitive_load.germane_load:.3f}")
            print(f"  • Overload Risk: {cognitive_load.overload_risk:.3f}")
            
            if cognitive_load.recommendations:
                print(f"  • Recommendations:")
                for rec in cognitive_load.recommendations:
                    print(f"    - {rec}")
            
            cognitive_results.append({
                "scenario": scenario["name"],
                "total_load": cognitive_load.total_load,
                "overload_risk": cognitive_load.overload_risk,
                "recommendations_count": len(cognitive_load.recommendations)
            })
        
        self.demo_results["demonstrations"]["cognitive_load"] = {
            "scenarios_tested": len(scenarios),
            "results": cognitive_results,
            "overload_detection_working": any(r["overload_risk"] > 0.5 for r in cognitive_results)
        }
    
    async def _demo_intervention_system(self):
        """Demonstrate intervention recommendation system"""
        print("\n" + "─"*60)
        print("🆘 4. INTERVENTION SYSTEM DEMONSTRATION")
        print("─"*60)
        
        student_id = "demo_student_intervention"
        concept_id = "organic_chemistry"
        
        print("Simulating a struggling student scenario...")
        
        # Create a scenario that should trigger intervention
        interventions_triggered = []
        
        # Simulate multiple consecutive errors
        for i in range(5):
            request = EnhancedTraceRequest(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=False,  # Consecutive failures
                difficulty=0.7,
                stress_level=0.6 + i * 0.08,  # Increasing stress
                cognitive_load=0.8,
                fatigue_level=0.5,
                response_time_ms=15000 + i * 3000  # Increasing response time
            )
            
            response = await self.bkt_service.trace_knowledge(request)
            
            print(f"  Attempt {i+1}: ❌ Failed | Mastery: {response.new_mastery:.3f} | "
                  f"Stress: {request.stress_level:.2f}")
            
            if response.intervention:
                print(f"    🚨 INTERVENTION TRIGGERED!")
                print(f"    Strategy: {response.intervention.strategy}")
                print(f"    Level: {response.intervention.level}")
                print(f"    Reason: {response.intervention.trigger_reason}")
                print(f"    Success Probability: {response.intervention.success_probability:.3f}")
                print(f"    Recommendations:")
                for rec in response.intervention.recommendations:
                    print(f"      - {rec}")
                
                interventions_triggered.append({
                    "attempt": i + 1,
                    "strategy": response.intervention.strategy,
                    "level": response.intervention.level.value,
                    "success_probability": response.intervention.success_probability
                })
                break
        
        # Also test cognitive overload intervention
        print("\nTesting cognitive overload intervention...")
        
        overload_request = EnhancedTraceRequest(
            student_id=f"{student_id}_overload",
            concept_id=concept_id,
            is_correct=False,
            difficulty=0.95,
            stress_level=0.9,
            cognitive_load=0.95,
            fatigue_level=0.85,
            time_pressure=1.8
        )
        
        overload_response = await self.bkt_service.trace_knowledge(overload_request)
        
        if overload_response.intervention:
            print(f"  🧠 COGNITIVE OVERLOAD INTERVENTION!")
            print(f"  Strategy: {overload_response.intervention.strategy}")
            print(f"  Recommendations:")
            for rec in overload_response.intervention.recommendations:
                print(f"    - {rec}")
            
            interventions_triggered.append({
                "type": "cognitive_overload",
                "strategy": overload_response.intervention.strategy,
                "level": overload_response.intervention.level.value
            })
        
        self.demo_results["demonstrations"]["interventions"] = {
            "interventions_triggered": len(interventions_triggered),
            "intervention_details": interventions_triggered,
            "system_responsive": len(interventions_triggered) > 0
        }
    
    async def _demo_advanced_analytics(self):
        """Demonstrate advanced analytics capabilities"""
        print("\n" + "─"*60)
        print("📊 5. ADVANCED ANALYTICS DEMONSTRATION")
        print("─"*60)
        
        # Generate some interaction data first
        student_id = "demo_student_analytics"
        concepts = ["basic_algebra", "quadratic_equations", "calculus_derivatives"]
        
        print("Generating interaction data for analytics...")
        
        for concept in concepts:
            print(f"  Learning {concept}...")
            for i in range(15):
                # Simulate realistic learning curve
                success_prob = 0.3 + min(0.6, i * 0.05)
                is_correct = i > 2 and (i <= 5 or success_prob > 0.7)  # Realistic pattern
                
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=concept,
                    is_correct=is_correct,
                    difficulty=0.4 + i * 0.03,
                    stress_level=max(0.1, 0.6 - i * 0.03),
                    cognitive_load=0.5 + (i % 3) * 0.1
                )
                
                await self.bkt_service.trace_knowledge(request)
        
        print("\nGenerating analytics reports...")
        
        # 1. System evaluation
        eval_request = BKTEvaluationRequest(
            student_id=student_id,
            min_interactions=5
        )
        eval_response = await self.bkt_service.evaluate_system(eval_request)
        
        print(f"\n📈 System Evaluation Results:")
        print(f"  • Next-step AUC: {eval_response.next_step_auc:.3f}")
        print(f"  • Next-step Accuracy: {eval_response.next_step_accuracy:.3f}")
        print(f"  • Brier Score: {eval_response.brier_score:.3f}")
        print(f"  • Overall Quality: {eval_response.overall_quality_score:.3f}")
        print(f"  • Recommendation: {eval_response.recommendation}")
        
        # 2. Student profile
        profile_request = StudentProfileRequest(
            student_id=student_id,
            include_concept_details=True,
            include_learning_analytics=True
        )
        profile_response = await self.bkt_service.get_student_profile(profile_request)
        
        print(f"\n👤 Student Profile Results:")
        print(f"  • Overall Performance: {profile_response.overall_performance:.3f}")
        print(f"  • Learning Velocity: {profile_response.learning_velocity:.3f} concepts/day")
        print(f"  • Stress Resilience: {profile_response.stress_resilience:.3f}")
        print(f"  • Cognitive Load Tolerance: {profile_response.cognitive_load_tolerance:.3f}")
        print(f"  • Exam Readiness: {profile_response.exam_readiness_score:.3f}")
        
        print(f"\n📚 Concept Mastery Details:")
        for concept_id, mastery in profile_response.concept_masteries.items():
            print(f"  • {concept_id}: {mastery.mastery_probability:.3f} "
                  f"(confidence: {mastery.confidence_level:.3f})")
        
        if profile_response.focus_recommendations:
            print(f"\n💡 Focus Recommendations:")
            for rec in profile_response.focus_recommendations:
                print(f"  • {rec}")
        
        # 3. System analytics
        analytics_request = SystemAnalyticsRequest(time_window_days=1)
        analytics_response = await self.bkt_service.get_system_analytics(analytics_request)
        
        print(f"\n🔧 System Analytics:")
        print(f"  • Overall Accuracy: {analytics_response.overall_prediction_accuracy:.3f}")
        print(f"  • System Health: {analytics_response.system_health_score:.3f}")
        print(f"  • Key Insights:")
        for insight in analytics_response.key_insights:
            print(f"    - {insight}")
        
        self.demo_results["demonstrations"]["analytics"] = {
            "system_evaluation": {
                "next_step_auc": eval_response.next_step_auc,
                "next_step_accuracy": eval_response.next_step_accuracy,
                "overall_quality": eval_response.overall_quality_score,
                "recommendation": eval_response.recommendation
            },
            "student_profile": {
                "overall_performance": profile_response.overall_performance,
                "learning_velocity": profile_response.learning_velocity,
                "exam_readiness": profile_response.exam_readiness_score,
                "concepts_tracked": len(profile_response.concept_masteries)
            },
            "system_health": analytics_response.system_health_score
        }
    
    async def _demo_multi_student_simulation(self):
        """Demonstrate multi-student simulation"""
        print("\n" + "─"*60)
        print("👥 6. MULTI-STUDENT SIMULATION DEMONSTRATION")
        print("─"*60)
        
        print(f"Simulating {len(self.demo_students)} students learning multiple concepts...")
        
        student_performances = {}
        
        for student_id in self.demo_students:
            print(f"\nProcessing student: {student_id}")
            student_performances[student_id] = {}
            
            # Each student learns 3 random concepts
            import random
            student_concepts = random.sample(list(self.demo_concepts.keys()), 3)
            
            for concept_id in student_concepts:
                concept_info = self.demo_concepts[concept_id]
                
                # Simulate individual learning patterns
                final_mastery = 0.0
                interactions = 0
                
                for i in range(10):
                    # Different students have different learning patterns
                    base_ability = hash(student_id) % 100 / 100  # Consistent per student
                    difficulty_factor = concept_info["difficulty"]
                    
                    # Success probability based on ability, difficulty, and practice
                    success_prob = base_ability + (i * 0.05) - difficulty_factor * 0.3
                    success_prob = max(0.1, min(0.9, success_prob))
                    
                    is_correct = random.random() < success_prob
                    
                    request = EnhancedTraceRequest(
                        student_id=student_id,
                        concept_id=concept_id,
                        is_correct=is_correct,
                        difficulty=difficulty_factor,
                        stress_level=random.uniform(0.2, 0.6),
                        cognitive_load=random.uniform(0.3, 0.7)
                    )
                    
                    response = await self.bkt_service.trace_knowledge(request)
                    final_mastery = response.new_mastery
                    interactions += 1
                
                student_performances[student_id][concept_id] = {
                    "final_mastery": final_mastery,
                    "interactions": interactions,
                    "difficulty": difficulty_factor
                }
                
                print(f"  {concept_id}: mastery = {final_mastery:.3f}")
        
        # Analyze results
        all_masteries = []
        high_performers = []
        
        for student_id, concepts in student_performances.items():
            avg_mastery = sum(c["final_mastery"] for c in concepts.values()) / len(concepts)
            all_masteries.append(avg_mastery)
            
            if avg_mastery >= 0.7:
                high_performers.append(student_id)
        
        avg_system_mastery = sum(all_masteries) / len(all_masteries)
        
        print(f"\n📊 Multi-Student Results:")
        print(f"  • Students simulated: {len(self.demo_students)}")
        print(f"  • Average mastery across all students: {avg_system_mastery:.3f}")
        print(f"  • High performers (≥0.7 mastery): {len(high_performers)}/{len(self.demo_students)}")
        print(f"  • Success rate: {len(high_performers)/len(self.demo_students)*100:.1f}%")
        
        self.demo_results["demonstrations"]["multi_student"] = {
            "students_simulated": len(self.demo_students),
            "average_mastery": avg_system_mastery,
            "high_performers": len(high_performers),
            "success_rate": len(high_performers)/len(self.demo_students),
            "individual_results": student_performances
        }
    
    async def _demo_system_performance(self):
        """Demonstrate system performance characteristics"""
        print("\n" + "─"*60)
        print("⚡ 7. SYSTEM PERFORMANCE DEMONSTRATION")
        print("─"*60)
        
        import time
        
        print("Testing system performance with rapid interactions...")
        
        # Performance test: measure processing times
        processing_times = []
        
        for i in range(50):  # 50 rapid interactions
            start_time = time.time()
            
            request = EnhancedTraceRequest(
                student_id=f"perf_student_{i % 5}",  # 5 different students
                concept_id=f"perf_concept_{i % 3}",  # 3 different concepts
                is_correct=i % 3 == 0,  # Varied performance
                difficulty=0.5,
                stress_level=0.3,
                cognitive_load=0.4
            )
            
            await self.bkt_service.trace_knowledge(request)
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            processing_times.append(processing_time)
        
        # Calculate performance metrics
        avg_time = sum(processing_times) / len(processing_times)
        min_time = min(processing_times)
        max_time = max(processing_times)
        
        # Get system status
        system_status = await self.bkt_service.get_system_status()
        
        print(f"\n⚡ Performance Results:")
        print(f"  • Interactions processed: {len(processing_times)}")
        print(f"  • Average processing time: {avg_time:.2f}ms")
        print(f"  • Min/Max processing time: {min_time:.2f}ms / {max_time:.2f}ms")
        print(f"  • Throughput: ~{1000/avg_time:.1f} requests/second")
        
        print(f"\n📊 System Status:")
        print(f"  • Service status: {system_status['service_status']}")
        print(f"  • Current accuracy: {system_status['current_accuracy']:.3f}")
        print(f"  • Requests processed: {system_status['requests_processed']}")
        print(f"  • Features enabled:")
        for feature, enabled in system_status['features_enabled'].items():
            print(f"    - {feature}: {'✅' if enabled else '❌'}")
        
        self.demo_results["demonstrations"]["performance"] = {
            "interactions_tested": len(processing_times),
            "average_processing_time_ms": avg_time,
            "min_processing_time_ms": min_time,
            "max_processing_time_ms": max_time,
            "estimated_throughput_rps": 1000/avg_time,
            "system_status": system_status
        }
    
    async def _generate_demo_summary(self):
        """Generate comprehensive demo summary"""
        print("\n" + "="*80)
        print("📋 ENHANCED BKT DEMO SUMMARY")
        print("="*80)
        
        # Extract key metrics
        basic_improvement = self.demo_results["demonstrations"]["basic_tracing"]["improvement"]
        transfer_benefit = self.demo_results["demonstrations"]["transfer_learning"]["transfer_benefit"]
        system_accuracy = self.demo_results["demonstrations"]["analytics"]["system_evaluation"]["next_step_accuracy"]
        avg_processing_time = self.demo_results["demonstrations"]["performance"]["average_processing_time_ms"]
        multi_student_success = self.demo_results["demonstrations"]["multi_student"]["success_rate"]
        
        print(f"\n🎯 KEY PERFORMANCE INDICATORS:")
        print(f"  • Knowledge Tracing Accuracy: {system_accuracy:.3f} ({'✅ EXCELLENT' if system_accuracy >= 0.9 else '⚠️ GOOD' if system_accuracy >= 0.8 else '❌ NEEDS WORK'})")
        print(f"  • Learning Improvement: {basic_improvement:.3f} mastery gain")
        print(f"  • Transfer Learning Benefit: +{transfer_benefit:.3f} initial boost")
        print(f"  • Multi-Student Success Rate: {multi_student_success*100:.1f}%")
        print(f"  • Average Processing Time: {avg_processing_time:.1f}ms")
        
        print(f"\n🔧 FEATURES DEMONSTRATED:")
        features_working = 0
        total_features = 7
        
        demos = self.demo_results["demonstrations"]
        
        if demos["basic_tracing"]["improvement"] > 0.1:
            print(f"  ✅ Basic Knowledge Tracing - Learning improvement detected")
            features_working += 1
        else:
            print(f"  ❌ Basic Knowledge Tracing - Insufficient improvement")
        
        if demos["transfer_learning"]["transfer_detected"]:
            print(f"  ✅ Transfer Learning - Cross-concept knowledge transfer working")
            features_working += 1
        else:
            print(f"  ❌ Transfer Learning - Transfer not detected")
        
        if demos["cognitive_load"]["overload_detection_working"]:
            print(f"  ✅ Cognitive Load Assessment - Overload detection functional")
            features_working += 1
        else:
            print(f"  ❌ Cognitive Load Assessment - Detection not working")
        
        if demos["interventions"]["system_responsive"]:
            print(f"  ✅ Intervention System - Recommendations triggered appropriately")
            features_working += 1
        else:
            print(f"  ❌ Intervention System - No interventions triggered")
        
        if demos["analytics"]["system_evaluation"]["next_step_accuracy"] > 0.7:
            print(f"  ✅ Advanced Analytics - Evaluation system functional")
            features_working += 1
        else:
            print(f"  ❌ Advanced Analytics - Evaluation accuracy too low")
        
        if demos["multi_student"]["success_rate"] > 0.5:
            print(f"  ✅ Multi-Student Simulation - System scales with multiple learners")
            features_working += 1
        else:
            print(f"  ❌ Multi-Student Simulation - Poor scalability")
        
        if demos["performance"]["average_processing_time_ms"] < 100:
            print(f"  ✅ System Performance - Fast response times achieved")
            features_working += 1
        else:
            print(f"  ❌ System Performance - Slow response times")
        
        feature_success_rate = features_working / total_features
        
        print(f"\n📊 OVERALL SYSTEM ASSESSMENT:")
        print(f"  • Features Working: {features_working}/{total_features} ({feature_success_rate*100:.1f}%)")
        
        if system_accuracy >= 0.9 and feature_success_rate >= 0.8:
            assessment = "🌟 EXCELLENT - Ready for production deployment"
        elif system_accuracy >= 0.8 and feature_success_rate >= 0.7:
            assessment = "✅ GOOD - Minor optimizations recommended"
        elif system_accuracy >= 0.7 and feature_success_rate >= 0.6:
            assessment = "⚠️ SATISFACTORY - Improvements needed"
        else:
            assessment = "❌ NEEDS WORK - Significant issues to address"
        
        print(f"  • System Status: {assessment}")
        
        print(f"\n💾 Demo results saved to: enhanced_bkt_demo_results.json")
        
        # Save results
        with open("enhanced_bkt_demo_results.json", "w") as f:
            json.dump(self.demo_results, f, indent=2, default=str)
        
        self.demo_results["summary"] = {
            "accuracy": system_accuracy,
            "features_working": features_working,
            "total_features": total_features,
            "feature_success_rate": feature_success_rate,
            "assessment": assessment,
            "production_ready": system_accuracy >= 0.9 and feature_success_rate >= 0.8
        }


async def main():
    """Main demo entry point"""
    print("🎓 Enhanced BKT System Demo Starting...")
    print("=" * 60)
    
    demo = EnhancedBKTDemo()
    
    try:
        await demo.run_comprehensive_demo()
        
        # Final summary
        summary = demo.demo_results.get("summary", {})
        if summary.get("production_ready", False):
            print("\n🎉 SUCCESS: Enhanced BKT System is ready for production!")
        else:
            print(f"\n⚠️ The system shows promise but needs refinement for production use.")
            print(f"Accuracy: {summary.get('accuracy', 0):.3f}, Features: {summary.get('feature_success_rate', 0)*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        logger.error(f"Demo failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())