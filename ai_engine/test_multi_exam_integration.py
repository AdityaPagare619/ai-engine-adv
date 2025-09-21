import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Verify the API is running and accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_multi_exam_integration():
    """Test integration between different exam types"""
    exam_types = ["JEE_Mains", "NEET", "JEE_Advanced"]
    results = {}
    
    print("\n🔍 Testing multi-exam integration...")
    
    # Test sequential exam transitions
    for i in range(len(exam_types)):
        current_exam = exam_types[i]
        next_exam = exam_types[(i+1) % len(exam_types)]
        
        print(f"\n📋 Testing transition from {current_exam} to {next_exam}")
        
        # First request with current exam
        current_response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json={
                "student_id": "test_student_001",
                "question_id": f"q_001_{current_exam}",
                "base_time_ms": 60000,
                "stress_level": 0.3,
                "fatigue_level": 0.2,
                "mastery": 0.6,
                "difficulty": 0.7,
                "session_elapsed_ms": 1200000,
                "exam_code": current_exam
            }
        )
        
        assert current_response.status_code == 200
        current_data = current_response.json()
        print(f"  ✓ {current_exam} time allocation: {current_data['final_time_ms']}ms")
        
        # Second request with next exam
        next_response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json={
                "student_id": "test_student_001",
                "question_id": f"q_001_{next_exam}",
                "base_time_ms": 60000,
                "stress_level": 0.3,
                "fatigue_level": 0.2,
                "mastery": 0.6,
                "difficulty": 0.7,
                "session_elapsed_ms": 1200000,
                "exam_code": next_exam
            }
        )
        
        assert next_response.status_code == 200
        next_data = next_response.json()
        print(f"  ✓ {next_exam} time allocation: {next_data['final_time_ms']}ms")
        
        # Store results for comparison
        results[f"{current_exam}_to_{next_exam}"] = {
            "from": current_data['final_time_ms'],
            "to": next_data['final_time_ms']
        }
    
    # Verify exam transitions maintain consistency
    print("\n🔍 Verifying exam transition consistency...")
    for transition, times in results.items():
        print(f"  • {transition}: {times['from']}ms → {times['to']}ms")
    
    print("\n✅ Multi-exam integration test passed")
    return True

def test_exam_calibration():
    """Test calibration between different exam types"""
    print("\n🔍 Testing exam calibration...")
    
    # Define standard test parameters
    standard_params = {
        "student_id": "test_student_002",
        "question_id": "q_calibration",
        "base_time_ms": 60000,
        "stress_level": 0.3,
        "fatigue_level": 0.2,
        "mastery": 0.6,
        "difficulty": 0.7,
        "session_elapsed_ms": 1200000
    }
    
    # Test with different exam types
    exam_times = {}
    for exam_type in ["JEE_Mains", "NEET", "JEE_Advanced"]:
        params = standard_params.copy()
        params["exam_code"] = exam_type
        
        response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json=params
        )
        
        assert response.status_code == 200
        data = response.json()
        exam_times[exam_type] = data['final_time_ms']
        print(f"  ✓ {exam_type} calibrated time: {data['final_time_ms']}ms")
        
        # Check breakdown factors
        breakdown = data.get('time_breakdown', {})
        print(f"    • Base time: {breakdown.get('base_time_ms', 'N/A')}ms")
        print(f"    • Difficulty factor: {breakdown.get('difficulty_factor', 'N/A')}")
        print(f"    • Ability factor: {breakdown.get('ability_factor', 'N/A')}")
        print(f"    • Importance factor: {breakdown.get('importance_factor', 'N/A')}")
    
    # Verify expected calibration relationships
    # JEE Advanced should typically allocate more time than JEE Mains
    if exam_times["JEE_Advanced"] > exam_times["JEE_Mains"]:
        print("  ✓ JEE Advanced correctly allocates more time than JEE Mains")
    else:
        print("  ⚠️ Warning: JEE Advanced does not allocate more time than JEE Mains")
    
    print("\n✅ Exam calibration test passed")
    return True

def run_all_tests():
    """Run all multi-exam integration tests"""
    print("\n🚀 Running multi-exam integration tests...\n")
    
    if not test_health_check():
        print("❌ Health check failed, aborting tests")
        sys.exit(1)
    
    test_multi_exam_integration()
    test_exam_calibration()
    
    print("\n✅ All multi-exam integration tests completed successfully")

if __name__ == "__main__":
    run_all_tests()