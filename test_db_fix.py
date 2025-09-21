#!/usr/bin/env python3
"""
Quick test to verify Supabase upsert fix works correctly
"""

import sys
import os

# Add AI engine to path
ai_engine_path = os.path.join(os.getcwd(), 'ai_engine', 'src')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

from enterprise_simulation_final import EnterpriseAIEngine
import random

def test_database_operations():
    """Test database operations with conflict resolution"""
    
    print("Testing Database Conflict Resolution...")
    
    # Initialize AI Engine
    ai_engine = EnterpriseAIEngine()
    
    if not ai_engine.supabase_client:
        print("❌ No Supabase connection available")
        return
    
    # Test data
    test_student_id = "test_student_conflict"
    test_concept_id = "test_calculus"
    
    print(f"Testing with student: {test_student_id}, concept: {test_concept_id}")
    
    # Simulate multiple interactions with same student/concept
    for i in range(3):
        print(f"\n--- Interaction {i+1} ---")
        
        question_data = {
            'question_id': f'test_q_{i}',
            'topic': test_concept_id,
            'difficulty': random.uniform(0.3, 0.7)
        }
        
        student_response = {
            'correct': random.choice([True, False]),
            'response_time_ms': random.randint(2000, 8000)
        }
        
        bkt_update = {
            'previous_mastery': random.uniform(0.2, 0.6),
            'new_mastery': random.uniform(0.3, 0.8),
            'context_applied': {'test': True}
        }
        
        try:
            # This should work without conflicts now
            ai_engine._store_interaction_results(
                test_student_id, question_data, student_response, bkt_update
            )
            print(f"✅ Interaction {i+1} stored successfully")
            
        except Exception as e:
            print(f"❌ Interaction {i+1} failed: {e}")
    
    # Clean up test data
    try:
        ai_engine.supabase_client.table("bkt_knowledge_states").delete().eq(
            "student_id", test_student_id
        ).execute()
        print(f"\n🧹 Cleaned up test data for {test_student_id}")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n✅ Database conflict resolution test completed!")

if __name__ == "__main__":
    test_database_operations()