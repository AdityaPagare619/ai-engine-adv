#!/usr/bin/env python3
"""
Comprehensive test comparing original vs improved BKT performance
"""

import sys
import os
import numpy as np
from typing import List, Dict, Any

# Add AI engine to path
ai_engine_path = os.path.join(os.getcwd(), 'ai_engine', 'src')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

from knowledge_tracing.bkt.bkt_engine import BKTEngine
from knowledge_tracing.bkt.improved_bkt_engine import ImprovedBKTEngine

def simulate_student_performance(engine, student_id: str, num_interactions: int = 30) -> Dict[str, Any]:
    """Simulate realistic student performance with both engines"""
    
    results = []
    concepts = ["mechanics", "thermodynamics", "calculus", "organic_chemistry", "genetics"]
    
    for i in range(num_interactions):
        # Simulate realistic learning progression
        # Student gets better over time but has occasional struggles
        base_success_prob = min(0.9, 0.4 + i * 0.015)  # Gradual improvement
        
        # Add some randomness for realistic performance
        if i % 7 == 0:  # Occasional bad day
            success_prob = base_success_prob * 0.6
        elif i % 11 == 0:  # Occasional good day
            success_prob = min(0.95, base_success_prob * 1.3)
        else:
            success_prob = base_success_prob
        
        correct = np.random.choice([True, False], p=[success_prob, 1 - success_prob])
        
        # Select concept (simulate focusing on different topics)
        concept = concepts[i % len(concepts)]
        
        # Realistic context factors
        stress_level = np.random.uniform(0.2, 0.8)
        cognitive_load = np.random.uniform(0.3, 0.7)
        time_pressure = np.random.uniform(0.8, 1.4)
        difficulty = np.random.uniform(0.2, 0.9)
        
        response = {'student_id': student_id, 'correct': correct}
        context = {
            'stress_level': stress_level,
            'cognitive_load': cognitive_load,
            'time_pressure_factor': time_pressure,
            'difficulty': difficulty
        }
        
        if hasattr(engine, 'get_concept_mastery'):  # Improved BKT
            result = engine.update(response, concept=concept, **context)
        else:  # Original BKT
            result = engine.update(response, **context)
        
        results.append({
            'interaction': i + 1,
            'correct': correct,
            'mastery': result['mastery'],
            'concept': concept if hasattr(engine, 'get_concept_mastery') else 'general',
            'success_prob_intended': success_prob,
            'stress_level': stress_level,
            'context': context
        })
    
    return {
        'student_id': student_id,
        'results': results,
        'final_mastery': results[-1]['mastery'],
        'final_concepts': engine.get_all_masteries() if hasattr(engine, 'get_all_masteries') else {'general': results[-1]['mastery']},
        'average_mastery': np.mean([r['mastery'] for r in results])
    }

def analyze_performance_metrics(original_results: Dict, improved_results: Dict) -> Dict[str, Any]:
    """Analyze and compare performance metrics between engines"""
    
    original_final = original_results['final_mastery']
    improved_final = improved_results['final_mastery']
    
    original_avg = original_results['average_mastery']
    improved_avg = improved_results['average_mastery']
    
    original_masteries = [r['mastery'] for r in original_results['results']]
    improved_masteries = [r['mastery'] for r in improved_results['results']]
    
    # Calculate learning speed (how quickly mastery increases)
    original_learning_speed = (original_masteries[-1] - original_masteries[0]) / len(original_masteries)
    improved_learning_speed = (improved_masteries[-1] - improved_masteries[0]) / len(improved_masteries)
    
    # Calculate stability (consistency of mastery progression)
    original_stability = 1 / (1 + np.std(np.diff(original_masteries)))
    improved_stability = 1 / (1 + np.std(np.diff(improved_masteries)))
    
    # Calculate responsiveness (how well it responds to correct vs incorrect answers)
    original_responsiveness = calculate_responsiveness(original_results['results'])
    improved_responsiveness = calculate_responsiveness(improved_results['results'])
    
    return {
        'final_mastery': {
            'original': original_final,
            'improved': improved_final,
            'improvement': improved_final - original_final,
            'improvement_percent': ((improved_final - original_final) / original_final * 100) if original_final > 0 else 0
        },
        'average_mastery': {
            'original': original_avg,
            'improved': improved_avg,
            'improvement': improved_avg - original_avg,
            'improvement_percent': ((improved_avg - original_avg) / original_avg * 100) if original_avg > 0 else 0
        },
        'learning_speed': {
            'original': original_learning_speed,
            'improved': improved_learning_speed,
            'improvement': improved_learning_speed - original_learning_speed,
            'improvement_percent': ((improved_learning_speed - original_learning_speed) / abs(original_learning_speed) * 100) if original_learning_speed != 0 else 0
        },
        'stability': {
            'original': original_stability,
            'improved': improved_stability,
            'improvement': improved_stability - original_stability,
            'improvement_percent': ((improved_stability - original_stability) / original_stability * 100) if original_stability > 0 else 0
        },
        'responsiveness': {
            'original': original_responsiveness,
            'improved': improved_responsiveness,
            'improvement': improved_responsiveness - original_responsiveness,
            'improvement_percent': ((improved_responsiveness - original_responsiveness) / original_responsiveness * 100) if original_responsiveness > 0 else 0
        }
    }

def calculate_responsiveness(results: List[Dict]) -> float:
    """Calculate how responsive the BKT is to student performance"""
    correct_gains = []
    incorrect_losses = []
    
    for i in range(1, len(results)):
        prev_mastery = results[i-1]['mastery']
        curr_mastery = results[i]['mastery']
        mastery_change = curr_mastery - prev_mastery
        
        if results[i]['correct']:
            correct_gains.append(mastery_change)
        else:
            incorrect_losses.append(-mastery_change)  # Make positive for analysis
    
    if not correct_gains or not incorrect_losses:
        return 0.5
    
    avg_gain = np.mean(correct_gains) if correct_gains else 0
    avg_loss = np.mean(incorrect_losses) if incorrect_losses else 0
    
    # Good responsiveness = decent gains on correct, reasonable losses on incorrect
    responsiveness = (avg_gain + avg_loss) / 2 if (avg_gain + avg_loss) > 0 else 0.1
    return min(1.0, responsiveness * 10)  # Scale to 0-1 range

def run_comprehensive_comparison():
    """Run comprehensive comparison between original and improved BKT"""
    
    print("=== COMPREHENSIVE BKT IMPROVEMENT ANALYSIS ===\n")
    
    # Test with multiple students to get robust results
    num_students = 5
    interactions_per_student = 50
    
    original_results = []
    improved_results = []
    
    for student_num in range(num_students):
        student_id = f"test_student_{student_num}"
        
        print(f"Testing student {student_num + 1}/{num_students}: {student_id}")
        
        # Test original BKT
        original_bkt = BKTEngine('NEET')
        original_result = simulate_student_performance(original_bkt, student_id, interactions_per_student)
        original_results.append(original_result)
        
        # Test improved BKT
        improved_bkt = ImprovedBKTEngine('NEET')
        improved_result = simulate_student_performance(improved_bkt, student_id, interactions_per_student)
        improved_results.append(improved_result)
    
    # Analyze results
    print(f"\n=== PERFORMANCE ANALYSIS ===\n")
    
    all_metrics = []
    for i in range(num_students):
        metrics = analyze_performance_metrics(original_results[i], improved_results[i])
        all_metrics.append(metrics)
        
        print(f"Student {i+1} Results:")
        print(f"  Final Mastery: {original_results[i]['final_mastery']:.3f} → {improved_results[i]['final_mastery']:.3f} (Δ{metrics['final_mastery']['improvement']:+.3f})")
        print(f"  Learning Speed: {metrics['learning_speed']['improvement_percent']:+.1f}% improvement")
        print(f"  Stability: {metrics['stability']['improvement_percent']:+.1f}% improvement")
        print(f"  Responsiveness: {metrics['responsiveness']['improvement_percent']:+.1f}% improvement")
        
        # Show concept-specific masteries for improved BKT
        if hasattr(improved_results[i], 'final_concepts'):
            print(f"  Final Concept Masteries: {improved_results[i]['final_concepts']}")
        print()
    
    # Calculate aggregate improvements
    avg_final_improvement = np.mean([m['final_mastery']['improvement'] for m in all_metrics])
    avg_learning_speed_improvement = np.mean([m['learning_speed']['improvement_percent'] for m in all_metrics])
    avg_stability_improvement = np.mean([m['stability']['improvement_percent'] for m in all_metrics])
    avg_responsiveness_improvement = np.mean([m['responsiveness']['improvement_percent'] for m in all_metrics])
    
    print(f"=== AGGREGATE IMPROVEMENTS ===")
    print(f"Average Final Mastery Improvement: {avg_final_improvement:+.3f} ({avg_final_improvement/0.6*100:+.1f}% relative to starting prior)")
    print(f"Average Learning Speed Improvement: {avg_learning_speed_improvement:+.1f}%")
    print(f"Average Stability Improvement: {avg_stability_improvement:+.1f}%")
    print(f"Average Responsiveness Improvement: {avg_responsiveness_improvement:+.1f}%")
    
    # Overall assessment
    overall_improvement = (avg_learning_speed_improvement + avg_stability_improvement + avg_responsiveness_improvement) / 3
    print(f"\nOVERALL BKT IMPROVEMENT: {overall_improvement:+.1f}%")
    
    if overall_improvement > 30:
        assessment = "EXCELLENT - Major improvement achieved"
    elif overall_improvement > 15:
        assessment = "GOOD - Significant improvement"
    elif overall_improvement > 5:
        assessment = "MODERATE - Some improvement"
    else:
        assessment = "MINIMAL - Limited improvement"
    
    print(f"ASSESSMENT: {assessment}")
    
    # Specific improvements summary
    print(f"\n=== KEY IMPROVEMENTS IN IMPROVED BKT ===")
    print(f"✅ Lower initial prior (0.25 vs 0.6) - more realistic starting point")
    print(f"✅ Higher learning rate (0.35 vs 0.2) - faster adaptation")
    print(f"✅ Reduced context penalties - less over-penalization")
    print(f"✅ Student-specific adaptation - personalized learning rates")
    print(f"✅ Multi-concept tracking - separate mastery per topic")
    print(f"✅ Transfer learning - related concepts boost each other")
    print(f"✅ Recovery mechanisms - help for struggling students")
    print(f"✅ Confidence tracking - reliability estimation")
    
    return all_metrics

if __name__ == "__main__":
    metrics = run_comprehensive_comparison()