# ai_engine/test_time_allocation.py
import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_time_allocation(exam_code: str, base_time_ms: int):
    """Test time allocation for a specific exam type."""
    try:
        payload = {
            "student_id": "test_student_001",
            "question_id": "q_001",
            "base_time_ms": base_time_ms,
            "stress_level": 0.3,
            "fatigue_level": 0.2,
            "mastery": 0.7,
            "difficulty": 0.8,
            "session_elapsed_ms": 1800000,
            "exam_code": exam_code
        }
        
        response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            max_allowed = data.get("breakdown", {}).get("max_allowed_time_ms", 0)
            final_time = data.get("final_time_ms", 0)
            
            print(f"✅ Time allocation for {exam_code} passed")
            print(f"   Base time: {base_time_ms}ms")
            print(f"   Final time: {final_time}ms")
            print(f"   Max allowed: {max_allowed}ms")
            
            # Verify time constraints are enforced
            if exam_code == "JEE_Mains" and final_time > 180000:
                print(f"❌ Time exceeds JEE_Mains limit of 180000ms")
                return False
            elif exam_code == "NEET" and final_time > 90000:
                print(f"❌ Time exceeds NEET limit of 90000ms")
                return False
            elif exam_code == "JEE_Advanced" and final_time > 240000:
                print(f"❌ Time exceeds JEE_Advanced limit of 240000ms")
                return False
                
            return True
        else:
            print(f"❌ Time allocation for {exam_code} failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Time allocation for {exam_code} failed with error: {e}")
        return False

def run_tests():
    """Run all time allocation tests."""
    print("🔍 Testing Time Allocation...")
    
    # Test time allocation for all exam types with extreme base time
    exam_configs = [
        {"exam_code": "JEE_Mains", "base_time_ms": 600000},  # 10 minutes
        {"exam_code": "NEET", "base_time_ms": 600000},       # 10 minutes
        {"exam_code": "JEE_Advanced", "base_time_ms": 600000} # 10 minutes
    ]
    
    all_passed = True
    for config in exam_configs:
        if not test_time_allocation(**config):
            all_passed = False
    
    if all_passed:
        print("✅ All time allocation tests passed")
    else:
        print("❌ Some time allocation tests failed")
    
    return all_passed

if __name__ == "__main__":
    run_tests()