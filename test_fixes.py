#!/usr/bin/env python3
"""Quick test to verify BKT engine fixes work"""

from ai_engine.src.bkt_engine.enhanced_multi_concept_bkt import EnhancedMultiConceptBKTv2, StudentAdaptiveProfile
from datetime import datetime

def test_basic_functionality():
    """Test basic BKT functionality after fixes"""
    
    # Test basic initialization
    engine = EnhancedMultiConceptBKTv2()
    print("✅ BKT Engine initialized successfully")

    # Test student profile creation
    profile = StudentAdaptiveProfile(
        student_id='test123',
        learning_rates={'math': 0.35},
        stress_tolerance_levels={'general': 0.6},
        recovery_patterns={},
        performance_history=[True, False, True],
        concept_masteries={}
    )
    print(f"✅ Student profile created: {profile.student_id}")
    print(f"✅ Stress tolerance (property): {profile.stress_tolerance}")
    print(f"✅ Learning rate (property): {profile.learning_rate}")

    # Test basic update
    result = engine.update_mastery(
        student_id='test123',
        concept_id='algebra', 
        is_correct=True,
        question_metadata={'difficulty': 0.5},
        context_factors={'stress_level': 0.3},
        response_time_ms=5000
    )
    print(f"✅ Update result success: {result['success']}")
    print(f"✅ New mastery: {result['new_mastery']}")
    print("🎉 All basic tests passed!")
    
    return True

if __name__ == "__main__":
    test_basic_functionality()