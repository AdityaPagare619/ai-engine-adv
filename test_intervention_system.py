#!/usr/bin/env python3
"""
Test for Performance Decline Recovery and Intervention System
Verifies that the intervention system correctly detects performance decline
and provides appropriate interventions
"""

import sys
import os
import asyncio
from typing import Dict, Any, List
import random

# Add the ai_engine source to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_engine', 'src'))

# Import the intervention manager
from ai_engine.src.knowledge_tracing.recovery.intervention_manager import (
    InterventionManager, 
    PerformanceMetrics,
    InterventionLevel
)

# Import BKT integration
from ai_engine.src.knowledge_tracing.bkt.integration import BKTInterventionIntegration

class MockBKTModel:
    """Mock BKT model for testing"""
    def __init__(self, concept_id: str):
        self.concept_id = concept_id
        self.mastery = 0.5
        
    async def update(self, student_id: str, correct: bool, response_time_ms: int, **kwargs):
        """Mock update method"""
        # Simple mastery update logic for testing
        if correct:
            self.mastery = min(1.0, self.mastery + 0.1)
        else:
            self.mastery = max(0.0, self.mastery - 0.1)
            
        return {
            "previous_mastery": self.mastery - (0.1 if correct else -0.1),
            "new_mastery": self.mastery,
            "learning_occurred": correct,
            "p_correct_pred": self.mastery
        }

class TestInterventionSystem:
    """Test the intervention system"""
    
    def __init__(self):
        self.intervention_manager = InterventionManager()
        self.bkt_integration = BKTInterventionIntegration()
        
    async def test_intervention_detection(self):
        """Test that interventions are detected correctly"""
        print("\n🔍 Testing intervention detection...")
        
        # Create a student with declining performance
        student_id = "student1"
        concept_id = "algebra_linear_equations"
        
        # Add some initial successful attempts
        for i in range(3):
            self.intervention_manager.add_performance_data(
                student_id=student_id,
                topic=concept_id,
                is_correct=True,
                response_time=2.0,  # 2 seconds
                difficulty=0.5,
                mastery_before=0.4 + (i * 0.1),
                mastery_after=0.5 + (i * 0.1),
                time_pressure=0.2,
                fatigue=0.1
            )
        
        # No intervention should be triggered yet
        intervention = self.intervention_manager.get_intervention(student_id, concept_id)
        print(f"After 3 correct answers: {'Intervention triggered' if intervention else 'No intervention'}")
        
        # Now add several consecutive failures with increasing response times
        for i in range(5):
            self.intervention_manager.add_performance_data(
                student_id=student_id,
                topic=concept_id,
                is_correct=False,
                response_time=3.0 + i,  # Increasing response times
                difficulty=0.5,
                mastery_before=0.7 - (i * 0.1),
                mastery_after=0.6 - (i * 0.1),
                time_pressure=0.5,
                fatigue=0.3 + (i * 0.1)
            )
        
        # Now intervention should be triggered
        intervention = self.intervention_manager.get_intervention(student_id, concept_id)
        if intervention:
            print(f"✅ Intervention correctly triggered after performance decline")
            print(f"   Strategy: {intervention.strategy_applied.name}")
            print(f"   Level: {intervention.strategy_applied.level.name}")
            print(f"   Success probability: {intervention.success_probability:.2f}")
            print(f"   Recommendations:")
            for rec in intervention.recommendations:
                print(f"   - {rec}")
        else:
            print("❌ Failed to trigger intervention after performance decline")
            
        return intervention is not None
    
    async def test_bkt_integration(self):
        """Test integration with BKT system"""
        print("\n🔄 Testing BKT integration...")
        
        student_id = "student2"
        concept_id = "physics_kinematics"
        
        # Create mock BKT model
        bkt_model = MockBKTModel(concept_id)
        intervention = None
        
        # Simulate a series of responses
        # First some successful attempts
        for i in range(3):
            result = await bkt_model.update(student_id, True, 2000)
            intervention = await self.bkt_integration.process_response(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=True,
                response_time_ms=2000,
                bkt_model=bkt_model,
                bkt_result=result,
                question_difficulty=0.5,
                time_pressure=0.2
            )
            
        print(f"After 3 correct answers: {'Intervention triggered' if intervention else 'No intervention'}")
        
        # Then a series of failures with increasing response times and time pressure
        for i in range(5):
            result = await bkt_model.update(student_id, False, 3000 + i * 1000)
            intervention = await self.bkt_integration.process_response(
                student_id=student_id,
                concept_id=concept_id,
                is_correct=False,
                response_time_ms=3000 + i * 1000,
                bkt_model=bkt_model,
                bkt_result=result,
                question_difficulty=0.5,
                time_pressure=0.5 + i * 0.1
            )
            
        if intervention:
            print(f"✅ BKT integration correctly triggered intervention")
            print(f"   Strategy: {intervention.strategy_applied.name}")
            print(f"   Level: {intervention.strategy_applied.level.name}")
            print(f"   Success probability: {intervention.success_probability:.2f}")
        else:
            print("❌ BKT integration failed to trigger intervention")
            
        return intervention is not None
    
    async def test_intervention_levels(self):
        """Test different intervention levels based on severity"""
        print("\n📊 Testing intervention levels...")
        
        results = []
        
        # Test different scenarios with varying severity
        scenarios = [
            {
                "name": "Mild decline",
                "correct_ratio": 0.6,  # 60% correct
                "consecutive_failures": 2,
                "time_pressure": 0.3,
                "fatigue": 0.3,
                "expected_level": InterventionLevel.MILD
            },
            {
                "name": "Moderate decline",
                "correct_ratio": 0.4,  # 40% correct
                "consecutive_failures": 3,
                "time_pressure": 0.5,
                "fatigue": 0.5,
                "expected_level": InterventionLevel.MODERATE
            },
            {
                "name": "Severe decline",
                "correct_ratio": 0.2,  # 20% correct
                "consecutive_failures": 4,
                "time_pressure": 0.7,
                "fatigue": 0.7,
                "expected_level": InterventionLevel.STRONG
            },
            {
                "name": "Critical decline",
                "correct_ratio": 0.0,  # 0% correct
                "consecutive_failures": 5,
                "time_pressure": 0.9,
                "fatigue": 0.9,
                "expected_level": InterventionLevel.CRITICAL
            }
        ]
        
        for i, scenario in enumerate(scenarios):
            student_id = f"student_scenario_{i}"
            concept_id = "test_concept"
            
            # Reset intervention manager for clean test
            intervention_manager = InterventionManager()
            
            # Add performance data according to scenario
            for j in range(5):
                is_correct = random.random() < scenario["correct_ratio"]
                # Make sure we end with consecutive failures
                if j >= (5 - scenario["consecutive_failures"]):
                    is_correct = False
                    
                intervention_manager.add_performance_data(
                    student_id=student_id,
                    topic=concept_id,
                    is_correct=is_correct,
                    response_time=2.0 + (0.5 * j if not is_correct else 0),
                    difficulty=0.5,
                    mastery_before=0.5,
                    mastery_after=0.5 + (0.1 if is_correct else -0.1),
                    time_pressure=scenario["time_pressure"],
                    fatigue=scenario["fatigue"]
                )
            
            # Get intervention
            intervention = intervention_manager.get_intervention(student_id, concept_id)
            
            if intervention:
                actual_level = intervention.strategy_applied.level
                success = actual_level == scenario["expected_level"]
                results.append(success)
                
                status = "✅" if success else "❌"
                print(f"{status} {scenario['name']}: Expected {scenario['expected_level'].name}, got {actual_level.name}")
            else:
                print(f"❌ {scenario['name']}: No intervention triggered")
                results.append(False)
                
        success_rate = sum(results) / len(results) if results else 0
        print(f"\nIntervention level test success rate: {success_rate * 100:.1f}%")
        return success_rate >= 0.75  # At least 75% success rate
        
async def main():
    """Run all tests"""
    print("🧪 Starting Intervention System Tests")
    
    test_system = TestInterventionSystem()
    
    # Run tests
    detection_result = await test_system.test_intervention_detection()
    integration_result = await test_system.test_bkt_integration()
    levels_result = await test_system.test_intervention_levels()
    
    # Summarize results
    print("\n📋 Test Results Summary:")
    print(f"Intervention Detection: {'✅ PASS' if detection_result else '❌ FAIL'}")
    print(f"BKT Integration: {'✅ PASS' if integration_result else '❌ FAIL'}")
    print(f"Intervention Levels: {'✅ PASS' if levels_result else '❌ FAIL'}")
    
    overall_success = all([detection_result, integration_result, levels_result])
    print(f"\n{'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())