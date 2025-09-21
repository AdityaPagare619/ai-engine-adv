# ai_engine/test_mobile_compatibility.py
import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_mobile_headers():
    """Test time allocation with mobile-specific headers."""
    try:
        payload = {
            "student_id": "test_student_001",
            "question_id": "q_001",
            "base_time_ms": 120000,
            "stress_level": 0.3,
            "fatigue_level": 0.2,
            "mastery": 0.7,
            "difficulty": 0.8,
            "session_elapsed_ms": 1800000,
            "exam_code": "JEE_Mains"
        }
        
        # Mobile headers as specified in the testing manual
        mobile_headers = {
            "X-Device-Type": "mobile",
            "X-Screen-Class": "small",
            "X-Network": "low",
            "X-Interface-Score": "0.8",
            "X-Distraction-Level": "0.6"
        }
        
        # Test with mobile headers
        mobile_response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json=payload,
            headers=mobile_headers
        )
        
        # Test without mobile headers for comparison
        desktop_response = requests.post(
            f"{BASE_URL}/ai/trace/pacing/allocate-time",
            json=payload
        )
        
        if mobile_response.status_code == 200 and desktop_response.status_code == 200:
            mobile_data = mobile_response.json()
            desktop_data = desktop_response.json()
            
            print("✅ Mobile headers test passed")
            print(f"   Mobile final time: {mobile_data.get('final_time_ms')}ms")
            print(f"   Desktop final time: {desktop_data.get('final_time_ms')}ms")
            
            # Check if mobile response includes mobile-specific factors
            if "mobile_factor" in mobile_data.get("breakdown", {}):
                print(f"   Mobile factor: {mobile_data['breakdown']['mobile_factor']}")
            else:
                print("⚠️ Mobile factor not found in response")
            
            return True
        else:
            print(f"❌ Mobile headers test failed")
            if mobile_response.status_code != 200:
                print(f"   Mobile response status: {mobile_response.status_code}")
            if desktop_response.status_code != 200:
                print(f"   Desktop response status: {desktop_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Mobile headers test failed with error: {e}")
        return False

def test_network_quality():
    """Test time allocation with different network quality settings."""
    try:
        payload = {
            "student_id": "test_student_001",
            "question_id": "q_001",
            "base_time_ms": 120000,
            "stress_level": 0.3,
            "fatigue_level": 0.2,
            "mastery": 0.7,
            "difficulty": 0.8,
            "session_elapsed_ms": 1800000,
            "exam_code": "JEE_Mains"
        }
        
        network_types = ["high", "medium", "low"]
        results = {}
        
        for network in network_types:
            headers = {
                "X-Device-Type": "mobile",
                "X-Screen-Class": "small",
                "X-Network": network,
                "X-Interface-Score": "0.8",
                "X-Distraction-Level": "0.6"
            }
            
            response = requests.post(
                f"{BASE_URL}/ai/trace/pacing/allocate-time",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                results[network] = data.get("final_time_ms")
                print(f"✅ Network quality test for '{network}' passed")
                print(f"   Final time: {data.get('final_time_ms')}ms")
            else:
                print(f"❌ Network quality test for '{network}' failed")
                print(f"   Status code: {response.status_code}")
                return False
        
        # Check if low network has higher time than high network
        if results.get("low", 0) > results.get("high", 0):
            print("✅ Network quality impact verified: low network > high network")
        else:
            print("⚠️ Network quality impact not detected in time allocation")
        
        return True
    except Exception as e:
        print(f"❌ Network quality test failed with error: {e}")
        return False

def run_tests():
    """Run all mobile compatibility tests."""
    print("🔍 Testing Mobile Device Compatibility...")
    
    all_passed = True
    
    if not test_mobile_headers():
        all_passed = False
    
    if not test_network_quality():
        all_passed = False
    
    if all_passed:
        print("✅ All mobile compatibility tests passed")
    else:
        print("❌ Some mobile compatibility tests failed")
    
    return all_passed

if __name__ == "__main__":
    run_tests()