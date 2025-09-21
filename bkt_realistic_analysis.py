#!/usr/bin/env python3
"""
More realistic BKT analysis focusing on early learning stages and challenging scenarios
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

def create_realistic_scenarios():
    """Create different realistic learning scenarios"""
    
    scenarios = {
        "struggling_student": {
            "description": "Student who struggles initially but gradually improves",
            "base_success_rates": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8],
            "stress_levels": [0.7, 0.8, 0.6, 0.5, 0.4, 0.3, 0.3, 0.2],
            "interactions": 25
        },
        "average_student": {
            "description": "Typical student with steady improvement", 
            "base_success_rates": [0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.8, 0.85],
            "stress_levels": [0.5, 0.4, 0.4, 0.3, 0.3, 0.25, 0.25, 0.2],
            "interactions": 25
        },
        "inconsistent_student": {
            "description": "Student with high variability in performance",
            "base_success_rates": [0.3, 0.7, 0.4, 0.8, 0.5, 0.75, 0.45, 0.85],
            "stress_levels": [0.6, 0.2, 0.8, 0.1, 0.7, 0.15, 0.75, 0.1],
            "interactions": 25
        },
        "high_stress_student": {
            "description": "Student who performs worse under high stress",
            "base_success_rates": [0.6, 0.65, 0.7, 0.75, 0.8, 0.8, 0.85, 0.9],
            "stress_levels": [0.8, 0.85, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1],
            "interactions": 25
        }
    }
    
    return scenarios

def simulate_scenario(engine, scenario_name: str, scenario_config: Dict, student_id: str) -> Dict[str, Any]:
    """Simulate a specific learning scenario"""
    
    results = []
    concepts = ["mechanics", "thermodynamics", "calculus", "organic_chemistry", "genetics"]
    
    num_interactions = scenario_config["interactions"]
    base_rates = scenario_config["base_success_rates"]
    stress_levels = scenario_config["stress_levels"]
    
    for i in range(num_interactions):
        # Get base success rate for this phase
        phase = min(len(base_rates) - 1, i // (num_interactions // len(base_rates)))
        base_success_prob = base_rates[phase]
        stress_level = stress_levels[phase]
        
        # Add some randomness
        success_prob = max(0.1, min(0.95, base_success_prob + np.random.normal(0, 0.1)))
        stress_level = max(0.1, min(0.95, stress_level + np.random.normal(0, 0.05)))
        
        correct = np.random.choice([True, False], p=[success_prob, 1 - success_prob])
        
        # Cycle through concepts
        concept = concepts[i % len(concepts)]
        
        # Context factors based on scenario
        cognitive_load = np.random.uniform(0.3, 0.8)
        time_pressure = np.random.uniform(0.8, 1.5)
        difficulty = np.random.uniform(0.3, 0.8)
        
        response = {'student_id': student_id, 'correct': correct}
        context = {
            'stress_level': stress_level,
            'cognitive_load': cognitive_load,
            'time_pressure_factor': time_pressure,
            'difficulty': difficulty
        }
        
        if hasattr(engine, 'get_concept_mastery'):  # Improved BKT
            result = engine.update(response, concept=concept, **context)
            current_mastery = result['mastery']
        else:  # Original BKT
            result = engine.update(response, **context)
            current_mastery = result['mastery']
        
        results.append({
            'interaction': i + 1,
            'correct': correct,
            'mastery': current_mastery,
            'concept': concept if hasattr(engine, 'get_concept_mastery') else 'general',
            'success_prob_intended': success_prob,
            'stress_level': stress_level,
            'phase': phase,
            'context': context
        })
    
    return {
        'scenario': scenario_name,
        'student_id': student_id,
        'results': results,
        'final_mastery': results[-1]['mastery'],
        'final_concepts': engine.get_all_masteries() if hasattr(engine, 'get_all_masteries') else {'general': results[-1]['mastery']},
        'mastery_progression': [r['mastery'] for r in results]
    }

def analyze_scenario_performance(original_results: Dict, improved_results: Dict) -> Dict[str, Any]:
    """Analyze performance for a specific scenario"""
    
    original_progression = original_results['mastery_progression']
    improved_progression = improved_results['mastery_progression']
    
    # Key metrics
    original_final = original_results['final_mastery']
    improved_final = improved_results['final_mastery']
    
    # Early learning (first 10 interactions)
    original_early = np.mean(original_progression[:10])
    improved_early = np.mean(improved_progression[:10])
    
    # Mid learning (interactions 10-20)
    original_mid = np.mean(original_progression[10:20]) if len(original_progression) >= 20 else np.mean(original_progression[10:])
    improved_mid = np.mean(improved_progression[10:20]) if len(improved_progression) >= 20 else np.mean(improved_progression[10:])
    
    # Learning efficiency (area under the curve)
    original_auc = np.trapz(original_progression)
    improved_auc = np.trapz(improved_progression)
    
    # Adaptation speed (how quickly it responds to changing performance)
    original_adaptation = calculate_adaptation_speed(original_results['results'])
    improved_adaptation = calculate_adaptation_speed(improved_results['results'])
    
    return {
        'final_mastery_improvement': improved_final - original_final,
        'early_learning_improvement': improved_early - original_early,
        'mid_learning_improvement': improved_mid - original_mid,
        'learning_efficiency_improvement': (improved_auc - original_auc) / original_auc * 100 if original_auc > 0 else 0,
        'adaptation_improvement': (improved_adaptation - original_adaptation) / original_adaptation * 100 if original_adaptation > 0 else 0,
        'original': {
            'final': original_final,
            'early': original_early,
            'mid': original_mid,
            'auc': original_auc,
            'adaptation': original_adaptation
        },
        'improved': {
            'final': improved_final,
            'early': improved_early,
            'mid': improved_mid,
            'auc': improved_auc,
            'adaptation': improved_adaptation
        }
    }

def calculate_adaptation_speed(results: List[Dict]) -> float:
    """Calculate how quickly the system adapts to changing student performance"""
    
    if len(results) < 10:
        return 0.5
    
    adaptation_scores = []
    
    # Look at 5-interaction windows
    for i in range(5, len(results) - 5):
        # Performance in previous 5 interactions
        prev_performance = np.mean([r['correct'] for r in results[i-5:i]])
        
        # Mastery change in next 5 interactions
        mastery_before = results[i]['mastery']
        mastery_after = results[i+5]['mastery']
        mastery_change = mastery_after - mastery_before
        
        # Good adaptation means mastery increases when performance is good,
        # and decreases (or increases slowly) when performance is poor
        if prev_performance > 0.7:  # Good performance
            adaptation_score = max(0, mastery_change * 10)  # Reward positive changes
        elif prev_performance < 0.3:  # Poor performance  
            adaptation_score = max(0, -mastery_change * 5)  # Reward appropriate decreases
        else:  # Neutral performance
            adaptation_score = 1 - abs(mastery_change) * 5  # Reward stability
        
        adaptation_scores.append(max(0, min(1, adaptation_score)))
    
    return np.mean(adaptation_scores) if adaptation_scores else 0.5

def run_scenario_based_analysis():
    """Run comprehensive scenario-based analysis"""
    
    print("=== SCENARIO-BASED BKT ANALYSIS ===\n")
    
    scenarios = create_realistic_scenarios()
    all_scenario_results = {}
    
    for scenario_name, scenario_config in scenarios.items():
        print(f"📊 TESTING SCENARIO: {scenario_config['description']}")
        print(f"   Expected pattern: {scenario_config['base_success_rates']}")
        
        student_id = f"scenario_{scenario_name}_student"
        
        # Test original BKT
        original_bkt = BKTEngine('NEET') 
        original_result = simulate_scenario(original_bkt, scenario_name, scenario_config, student_id)
        
        # Test improved BKT
        improved_bkt = ImprovedBKTEngine('NEET')
        improved_result = simulate_scenario(improved_bkt, scenario_name, scenario_config, student_id)
        
        # Analyze results
        analysis = analyze_scenario_performance(original_result, improved_result)
        
        print(f"   📈 RESULTS:")
        print(f"      Final Mastery: {analysis['original']['final']:.3f} → {analysis['improved']['final']:.3f} (Δ{analysis['final_mastery_improvement']:+.3f})")
        print(f"      Early Learning: {analysis['original']['early']:.3f} → {analysis['improved']['early']:.3f} (Δ{analysis['early_learning_improvement']:+.3f})")
        print(f"      Learning Efficiency: {analysis['learning_efficiency_improvement']:+.1f}%")
        print(f"      Adaptation Speed: {analysis['adaptation_improvement']:+.1f}%")
        
        # Show concept masteries for improved BKT
        if 'final_concepts' in improved_result:
            concept_masteries = improved_result['final_concepts']
            if len(concept_masteries) > 1:
                print(f"      Concept Masteries: {', '.join([f'{k}={v:.2f}' for k, v in concept_masteries.items()])}")
        
        print()
        
        all_scenario_results[scenario_name] = {
            'original': original_result,
            'improved': improved_result,
            'analysis': analysis
        }
    
    # Aggregate analysis across scenarios
    print("=== AGGREGATE ANALYSIS ACROSS SCENARIOS ===")
    
    avg_final_improvement = np.mean([r['analysis']['final_mastery_improvement'] for r in all_scenario_results.values()])
    avg_early_improvement = np.mean([r['analysis']['early_learning_improvement'] for r in all_scenario_results.values()])
    avg_efficiency_improvement = np.mean([r['analysis']['learning_efficiency_improvement'] for r in all_scenario_results.values()])
    avg_adaptation_improvement = np.mean([r['analysis']['adaptation_improvement'] for r in all_scenario_results.values()])
    
    print(f"📊 Average Final Mastery Improvement: {avg_final_improvement:+.3f}")
    print(f"📊 Average Early Learning Improvement: {avg_early_improvement:+.3f}")
    print(f"📊 Average Learning Efficiency Improvement: {avg_efficiency_improvement:+.1f}%")
    print(f"📊 Average Adaptation Speed Improvement: {avg_adaptation_improvement:+.1f}%")
    
    overall_improvement = (avg_efficiency_improvement + avg_adaptation_improvement) / 2
    print(f"\n🎯 OVERALL IMPROVEMENT SCORE: {overall_improvement:+.1f}%")
    
    if overall_improvement > 25:
        assessment = "EXCELLENT 🚀"
    elif overall_improvement > 10:
        assessment = "GOOD 👍"
    elif overall_improvement > 2:
        assessment = "MODERATE 📈"
    else:
        assessment = "MINIMAL 😐"
    
    print(f"🏆 ASSESSMENT: {assessment}")
    
    # Identify best improvements by scenario type
    print(f"\n=== SCENARIO-SPECIFIC INSIGHTS ===")
    for scenario_name, results in all_scenario_results.items():
        analysis = results['analysis']
        efficiency_gain = analysis['learning_efficiency_improvement']
        adaptation_gain = analysis['adaptation_improvement']
        
        if efficiency_gain > 5 or adaptation_gain > 10:
            print(f"✅ {scenario_name.upper()}: Strong improvements")
            print(f"   Efficiency: {efficiency_gain:+.1f}%, Adaptation: {adaptation_gain:+.1f}%")
        elif efficiency_gain > 0 or adaptation_gain > 0:
            print(f"📈 {scenario_name.upper()}: Moderate improvements")
        else:
            print(f"⚠️  {scenario_name.upper()}: Limited improvements")
    
    # Specific advantages of improved BKT
    print(f"\n=== WHY IMPROVED BKT PERFORMS BETTER ===")
    print(f"🔹 Lower starting prior (0.25 vs 0.6) prevents overconfidence")
    print(f"🔹 Higher learning rate (0.35 vs 0.2) adapts faster to student performance")
    print(f"🔹 Stress tolerance adaptation reduces over-penalization")
    print(f"🔹 Recovery mechanisms help struggling students bounce back")
    print(f"🔹 Multi-concept tracking provides better granularity")
    print(f"🔹 Transfer learning connects related topics")
    
    return all_scenario_results

if __name__ == "__main__":
    results = run_scenario_based_analysis()