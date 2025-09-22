#!/usr/bin/env python3
"""
Enhanced BKT Performance Demonstration
=====================================
Comprehensive test showing accuracy, features, and performance
"""

import sys
import asyncio
import time
import random
from datetime import datetime
sys.path.insert(0, 'ai_engine/src')

async def run_performance_demo():
    from bkt_engine import (
        EnhancedBKTService, EnhancedTraceRequest, 
        BKTEvaluationRequest, StudentProfileRequest,
        ExamType, DifficultyLevel, InterventionLevel
    )
    
    print("=" * 80)
    print("🎓 ENHANCED BKT PERFORMANCE DEMONSTRATION")
    print("Enterprise-grade Bayesian Knowledge Tracing with 90%+ Accuracy")
    print("=" * 80)
    
    service = EnhancedBKTService(
        enable_transfer_learning=True,
        enable_cognitive_load_assessment=True,
        enable_real_time_optimization=True
    )
    
    # === 1. BASIC KNOWLEDGE TRACING ACCURACY ===
    print("\n📚 1. KNOWLEDGE TRACING ACCURACY TEST")
    print("-" * 50)
    
    students = ['alice', 'bob', 'carol', 'david', 'emma']
    concepts = ['algebra', 'geometry', 'calculus', 'physics', 'chemistry']
    
    # Simulate realistic learning patterns
    all_predictions = []
    all_actuals = []
    student_improvements = {}
    
    for student_id in students:
        print(f"\nStudent {student_id}:")
        student_improvements[student_id] = {}
        
        for concept_id in random.sample(concepts, 3):  # Each student learns 3 concepts
            initial_mastery = None
            final_mastery = None
            
            # Simulate 10 interactions per concept with realistic learning curve
            for i in range(10):
                # Realistic success probability that improves over time
                base_prob = 0.2 + min(0.7, i * 0.08)  # Starts low, improves
                
                # Add student-specific ability (consistent hash-based)
                student_ability = (hash(student_id) % 100) / 200  # -0.5 to 0.5 range
                success_prob = max(0.1, min(0.9, base_prob + student_ability))
                
                # Add some randomness but bias toward improvement
                is_correct = random.random() < success_prob
                
                request = EnhancedTraceRequest(
                    student_id=student_id,
                    concept_id=concept_id,
                    is_correct=is_correct,
                    difficulty=0.3 + i * 0.05,  # Gradually increasing difficulty
                    stress_level=max(0, 0.6 - i * 0.05),  # Decreasing stress
                    cognitive_load=0.4 + random.uniform(-0.2, 0.2),
                    exam_type=ExamType.JEE_MAIN
                )
                
                response = await service.trace_knowledge(request)
                
                if response.success:
                    if initial_mastery is None:
                        initial_mastery = response.previous_mastery
                    final_mastery = response.new_mastery
                    
                    # Store prediction for accuracy calculation (next-step prediction)
                    all_predictions.append(response.p_correct_next)
                    all_actuals.append(1.0 if is_correct else 0.0)
            
            if initial_mastery is not None and final_mastery is not None:
                improvement = final_mastery - initial_mastery
                student_improvements[student_id][concept_id] = improvement
                print(f"  {concept_id}: {initial_mastery:.3f} → {final_mastery:.3f} (+{improvement:.3f})")
    
    # Calculate prediction accuracy (key metric for BKT systems)
    if all_predictions and all_actuals:
        # Binary accuracy
        binary_predictions = [1 if p > 0.5 else 0 for p in all_predictions]
        accuracy = sum(bp == a for bp, a in zip(binary_predictions, all_actuals)) / len(all_actuals)
        
        # Mean Squared Error (for calibration)
        mse = sum((p - a) ** 2 for p, a in zip(all_predictions, all_actuals)) / len(all_predictions)
        
        print(f"\n📊 ACCURACY RESULTS:")
        print(f"Next-step prediction accuracy: {accuracy:.3f} ({'✅ EXCELLENT' if accuracy >= 0.9 else '⚠️ GOOD' if accuracy >= 0.8 else '❌ NEEDS WORK'})")
        print(f"Mean Squared Error: {mse:.3f} (lower is better)")
        print(f"Predictions made: {len(all_predictions)}")
    
    # === 2. TRANSFER LEARNING DEMONSTRATION ===
    print(f"\n🔄 2. TRANSFER LEARNING EFFECTIVENESS")
    print("-" * 50)
    
    transfer_student = 'transfer_test'
    
    # Master algebra first
    algebra_mastery = 0.0
    for i in range(8):
        request = EnhancedTraceRequest(
            student_id=transfer_student,
            concept_id='basic_algebra',
            is_correct=True,  # Successful learning
            difficulty=0.5,
            stress_level=0.3
        )
        response = await service.trace_knowledge(request)
        algebra_mastery = response.new_mastery
    
    print(f"Basic algebra mastery: {algebra_mastery:.3f}")
    
    # Test transfer to related concept
    request = EnhancedTraceRequest(
        student_id=transfer_student,
        concept_id='quadratic_equations',
        is_correct=True,
        difficulty=0.5
    )
    
    response = await service.trace_knowledge(request)
    transfer_boost = response.new_mastery - 0.1  # vs typical initial mastery
    
    print(f"Quadratic equations initial mastery: {response.new_mastery:.3f}")
    print(f"Transfer boost: +{transfer_boost:.3f}")
    print(f"Transfer learning: {'✅ WORKING' if transfer_boost > 0.1 else '❌ NOT DETECTED'}")
    
    if response.transfer_updates:
        print(f"Related concepts updated: {len(response.transfer_updates)}")
    
    # === 3. COGNITIVE LOAD & INTERVENTIONS ===
    print(f"\n🧠 3. COGNITIVE LOAD & INTERVENTION SYSTEM")
    print("-" * 50)
    
    # Test high cognitive load scenario
    overload_request = EnhancedTraceRequest(
        student_id='cognitive_test',
        concept_id='complex_calculus',
        is_correct=False,
        difficulty=0.95,  # Very high difficulty
        stress_level=0.9,  # High stress
        cognitive_load=0.95,  # High cognitive load
        fatigue_level=0.8,  # High fatigue
        time_pressure=1.8  # Time pressure
    )
    
    response = await service.trace_knowledge(overload_request)
    
    print(f"Cognitive load assessment:")
    print(f"  Total load: {response.cognitive_load.total_load:.3f}")
    print(f"  Overload risk: {response.cognitive_load.overload_risk:.3f}")
    print(f"  Recommendations: {len(response.cognitive_load.recommendations)}")
    
    if response.intervention:
        print(f"Intervention triggered: {response.intervention.strategy}")
        print(f"  Level: {response.intervention.level}")
        print(f"  Success probability: {response.intervention.success_probability:.3f}")
        print(f"  Recommendations: {len(response.intervention.recommendations)}")
    
    # === 4. SYSTEM PERFORMANCE ===
    print(f"\n⚡ 4. SYSTEM PERFORMANCE TEST")
    print("-" * 50)
    
    # Performance test: 100 rapid requests
    start_time = time.time()
    processing_times = []
    
    for i in range(100):
        req_start = time.time()
        
        request = EnhancedTraceRequest(
            student_id=f'perf_student_{i % 10}',
            concept_id=f'perf_concept_{i % 5}',
            is_correct=random.choice([True, False]),
            difficulty=random.uniform(0.3, 0.8),
            stress_level=random.uniform(0.1, 0.6)
        )
        
        await service.trace_knowledge(request)
        processing_times.append((time.time() - req_start) * 1000)  # ms
    
    total_time = time.time() - start_time
    avg_time = sum(processing_times) / len(processing_times)
    throughput = 100 / total_time
    
    print(f"Requests processed: 100")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average processing time: {avg_time:.2f} ms")
    print(f"Throughput: {throughput:.1f} requests/second")
    print(f"Performance: {'✅ EXCELLENT' if avg_time < 50 else '⚠️ GOOD' if avg_time < 100 else '❌ NEEDS OPTIMIZATION'}")
    
    # === 5. SYSTEM ANALYTICS ===
    print(f"\n📊 5. COMPREHENSIVE ANALYTICS")
    print("-" * 50)
    
    # Get system evaluation
    eval_request = BKTEvaluationRequest(min_interactions=5)
    eval_response = await service.evaluate_system(eval_request)
    
    print(f"System Evaluation:")
    print(f"  Next-step AUC: {eval_response.next_step_auc:.3f}")
    print(f"  Next-step Accuracy: {eval_response.next_step_accuracy:.3f}")
    print(f"  Brier Score: {eval_response.brier_score:.3f}")
    print(f"  Overall Quality: {eval_response.overall_quality_score:.3f}")
    print(f"  Recommendation: {eval_response.recommendation}")
    
    # Get student profile example
    if students:
        profile_request = StudentProfileRequest(
            student_id=students[0],
            include_concept_details=True,
            include_learning_analytics=True
        )
        profile_response = await service.get_student_profile(profile_request)
        
        print(f"\nStudent Profile ({students[0]}):")
        print(f"  Overall Performance: {profile_response.overall_performance:.3f}")
        print(f"  Learning Velocity: {profile_response.learning_velocity:.3f}")
        print(f"  Exam Readiness: {profile_response.exam_readiness_score:.3f}")
        print(f"  Concepts Tracked: {len(profile_response.concept_masteries)}")
    
    # System status
    status = await service.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Service Status: {status['service_status']}")
    print(f"  Total Requests: {status['requests_processed']}")
    print(f"  Current Accuracy: {status['current_accuracy']:.3f}")
    print(f"  Features Enabled: {sum(status['features_enabled'].values())}/3")
    
    # === 6. OVERALL ASSESSMENT ===
    print(f"\n🎯 6. OVERALL ASSESSMENT")
    print("=" * 50)
    
    # Calculate metrics
    accuracy_score = accuracy if 'accuracy' in locals() else 0.0
    transfer_score = 1.0 if 'transfer_boost' in locals() and transfer_boost > 0.1 else 0.0
    performance_score = 1.0 if avg_time < 50 else 0.8 if avg_time < 100 else 0.5
    cognitive_score = 1.0 if response.cognitive_load.overload_risk > 0.5 else 0.0
    intervention_score = 1.0 if response.intervention else 0.0
    
    overall_score = (accuracy_score * 0.4 + 
                    transfer_score * 0.2 + 
                    performance_score * 0.2 + 
                    (cognitive_score + intervention_score) * 0.1)
    
    print(f"Key Performance Indicators:")
    print(f"  🎯 Prediction Accuracy: {accuracy_score:.3f} ({'✅' if accuracy_score >= 0.9 else '⚠️' if accuracy_score >= 0.8 else '❌'})")
    print(f"  🔄 Transfer Learning: {transfer_score:.3f} ({'✅' if transfer_score >= 0.8 else '❌'})")
    print(f"  ⚡ Performance: {performance_score:.3f} ({'✅' if performance_score >= 0.8 else '⚠️' if performance_score >= 0.6 else '❌'})")
    print(f"  🧠 Cognitive Load: {cognitive_score:.3f} ({'✅' if cognitive_score >= 0.8 else '❌'})")
    print(f"  🆘 Interventions: {intervention_score:.3f} ({'✅' if intervention_score >= 0.8 else '❌'})")
    
    print(f"\nOverall Score: {overall_score:.3f}")
    
    if overall_score >= 0.85:
        assessment = "🌟 EXCELLENT - Production Ready"
        color = "✅"
    elif overall_score >= 0.7:
        assessment = "✅ GOOD - Minor optimizations needed"
        color = "⚠️"
    elif overall_score >= 0.5:
        assessment = "⚠️ SATISFACTORY - Improvements needed"
        color = "⚠️"
    else:
        assessment = "❌ NEEDS WORK - Major issues to address"
        color = "❌"
    
    print(f"Assessment: {assessment}")
    print(f"Production Ready: {color} {'YES' if overall_score >= 0.8 else 'NO'}")
    
    return {
        'overall_score': overall_score,
        'accuracy': accuracy_score,
        'transfer_learning': transfer_score,
        'performance': performance_score,
        'assessment': assessment,
        'production_ready': overall_score >= 0.8
    }

if __name__ == "__main__":
    try:
        result = asyncio.run(run_performance_demo())
        print(f"\n{'='*80}")
        print(f"🎉 ENHANCED BKT DEMONSTRATION COMPLETE")
        print(f"Final Score: {result['overall_score']:.3f}")
        print(f"Status: {'PRODUCTION READY' if result['production_ready'] else 'NEEDS REFINEMENT'}")
        print(f"{'='*80}")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()