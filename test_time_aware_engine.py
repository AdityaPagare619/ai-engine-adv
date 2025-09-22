#!/usr/bin/env python3
"""Test the Time-Aware Intelligence Engine"""

from ai_engine.src.bkt_engine.time_aware_engine import (
    TimeAwareExamEngine, 
    StudentClass, 
    ExamPhase,
    TimeAwareBKTIntegration
)
from datetime import datetime

def test_time_aware_engine():
    """Test time-aware exam preparation engine"""
    
    print("🎯 Testing Time-Aware Intelligence Engine")
    print("=" * 50)
    
    # Initialize engine
    time_engine = TimeAwareExamEngine()
    print("✅ Time-aware engine initialized")
    
    # Test exam timeline calculation for Class 12 student
    strategy = time_engine.calculate_exam_timeline(
        student_class=StudentClass.CLASS_12,
        target_exams=["JEE_MAIN", "JEE_ADVANCED"],
        preferred_attempt_year=2025
    )
    
    print(f"✅ Current Phase: {strategy.current_phase.value}")
    print(f"✅ Days remaining: {strategy.days_remaining}")
    print(f"✅ Recommended daily hours: {strategy.recommended_daily_hours}")
    print(f"✅ Priority concepts: {len(strategy.priority_concepts)} concepts")
    print(f"✅ Strategic milestones: {len(strategy.strategic_milestones)} milestones")
    
    # Test daily study plan generation
    student_masteries = {
        "calculus": 0.6,
        "algebra": 0.8,
        "mechanics": 0.4,
        "organic_chemistry": 0.7
    }
    
    daily_plan = time_engine.generate_daily_study_plan(
        strategy=strategy,
        student_masteries=student_masteries
    )
    
    print(f"✅ Daily plan generated for phase: {daily_plan['phase']}")
    print(f"✅ Total study hours: {daily_plan['total_study_hours']}")
    print(f"✅ Study topics: {len(daily_plan['study_topics'])}")
    print(f"✅ Motivation message: {daily_plan['motivation_message']}")
    
    # Test BKT integration
    bkt_integration = TimeAwareBKTIntegration(time_engine)
    adjustments = bkt_integration.get_context_adjustments(
        student_id="test_student",
        concept_id="calculus", 
        strategy=strategy
    )
    
    print(f"✅ BKT adjustments: {adjustments}")
    
    # Test different phases
    print("\n📅 Testing Different Exam Phases:")
    print("-" * 30)
    
    # Mock strategies for different phases
    phases = [ExamPhase.FOUNDATION, ExamPhase.BUILDING, ExamPhase.MASTERY, ExamPhase.CONFIDENCE]
    
    for phase in phases:
        strategy.current_phase = phase
        adjustments = bkt_integration.get_context_adjustments(
            student_id="test_student",
            concept_id="mechanics",
            strategy=strategy
        )
        print(f"{phase.value.upper()}: learn_rate_boost={adjustments['learn_rate_boost']}, "
              f"difficulty={adjustments['difficulty_preference']}")
    
    print("\n🎉 Time-Aware Engine Test Complete!")
    return True

if __name__ == "__main__":
    test_time_aware_engine()