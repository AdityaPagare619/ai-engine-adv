"""
Test script for Phase 4A BKT API Integration
Tests the demo API endpoints to verify Phase 4A functionality works correctly.
"""

import json
import sys
import os
from typing import Dict, Any

# Add ai_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_engine', 'src'))

# Import the demo API components directly for testing
from demo_api import app, repository
from fastapi.testclient import TestClient

class Phase4AAPITester:
    def __init__(self):
        self.client = TestClient(app)
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_health_check(self):
        """Test basic API health check"""
        response = self.client.get("/")
        passed = response.status_code == 200
        data = response.json() if passed else {}
        
        features_present = ("question_metadata_integration" in data.get("features", []) and
                          "adaptive_calibration" in data.get("features", []))
        
        self.log_test(
            "Health Check & Phase 4A Features",
            passed and features_present,
            f"Status: {response.status_code}, Features: {data.get('features', [])}"
        )
    
    def test_question_metadata_retrieval(self):
        """Test question metadata retrieval"""
        # Test existing question
        response = self.client.get("/ai/metadata/PHY_MECH_0001")
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_required_fields = all(field in data for field in 
                                    ["question_id", "difficulty_calibrated", "bloom_level"])
            passed = has_required_fields
            details = f"Metadata: {data}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("Question Metadata Retrieval (Existing)", passed, details)
        
        # Test non-existent question
        response = self.client.get("/ai/metadata/NONEXISTENT_Q001")
        passed = response.status_code == 404
        self.log_test("Question Metadata Retrieval (Not Found)", passed, 
                     f"Status: {response.status_code}")
    
    def test_basic_parameter_retrieval(self):
        """Test basic BKT parameter retrieval without question context"""
        response = self.client.get("/ai/concepts/test_concept/parameters")
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_params = "parameters" in data and "context_applied" in data
            is_basic = data.get("context_applied") == False
            passed = has_params and is_basic
            details = f"Context applied: {data.get('context_applied')}, Params: {data.get('parameters')}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("Basic Parameter Retrieval", passed, details)
    
    def test_contextual_parameter_retrieval(self):
        """Test BKT parameter retrieval with question context"""
        response = self.client.get("/ai/concepts/test_concept/parameters?question_id=PHY_MECH_0001")
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_context = data.get("context_applied") == True
            has_question_context = "question_context" in data
            passed = has_context and has_question_context
            details = f"Context applied: {has_context}, Question context present: {has_question_context}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("Contextual Parameter Retrieval", passed, details)
    
    def test_knowledge_state_basic(self):
        """Test basic knowledge state operations"""
        student_id = "test-student-001"
        concept_id = "test_concept"
        
        # Get initial state
        response = self.client.get(f"/ai/state/{student_id}/{concept_id}")
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            is_initial_state = data.get("mastery_probability") == 0.5
            practice_count_zero = data.get("practice_count") == 0
            passed = is_initial_state and practice_count_zero
            details = f"Initial mastery: {data.get('mastery_probability')}, Practice: {data.get('practice_count')}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("Knowledge State Retrieval", passed, details)
    
    def test_bkt_update_without_context(self):
        """Test BKT update without question context"""
        update_data = {
            "student_id": "test-student-002",
            "concept_id": "test_concept",
            "is_correct": True,
            "response_time_ms": 1500
        }
        
        response = self.client.post("/ai/trace/update", json=update_data)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_required_fields = all(field in data for field in 
                                    ["previous_mastery", "new_mastery", "parameters_used", "explanation"])
            mastery_increased = data.get("new_mastery", 0) > data.get("previous_mastery", 1)
            no_context = data.get("question_context") is None
            passed = has_required_fields and mastery_increased and no_context
            details = f"Mastery: {data.get('previous_mastery')} → {data.get('new_mastery')}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("BKT Update Without Context", passed, details)
    
    def test_bkt_update_with_context(self):
        """Test BKT update with question context (Phase 4A feature)"""
        update_data = {
            "student_id": "test-student-003",
            "concept_id": "test_concept",
            "question_id": "PHY_MECH_0001",  # This should trigger context lookup
            "is_correct": True,
            "response_time_ms": 2000
        }
        
        response = self.client.post("/ai/trace/update", json=update_data)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_context = data.get("question_context") is not None
            params_adjusted = data.get("explanation", {}).get("parameters_adjusted", False)
            has_adjustments = (data.get("explanation", {}).get("difficulty_adjustment", 0) != 0 or
                             data.get("explanation", {}).get("bloom_adjustment", 0) != 0)
            passed = has_context and params_adjusted and has_adjustments
            details = f"Context: {has_context}, Adjusted: {params_adjusted}, Adjustments: {has_adjustments}"
        else:
            details = f"Status: {response.status_code}"
        
        self.log_test("BKT Update With Context (Phase 4A)", passed, details)
    
    def test_parameter_adjustment_logic(self):
        """Test that parameter adjustments work correctly"""
        # Test with high difficulty question
        response1 = self.client.get("/ai/concepts/test_concept/parameters?question_id=PHY_MECH_0001")
        
        # Test with easy question (lower difficulty)
        response2 = self.client.get("/ai/concepts/test_concept/parameters?question_id=MATH_CALC_0001")
        
        passed = response1.status_code == 200 and response2.status_code == 200
        
        if passed:
            data1 = response1.json()
            data2 = response2.json()
            
            # PHY_MECH_0001 has difficulty 1.2, MATH_CALC_0001 has difficulty 0.8
            # Higher difficulty should lead to higher slip rate
            slip1 = data1.get("parameters", {}).get("slip_rate", 0)
            slip2 = data2.get("parameters", {}).get("slip_rate", 0)
            
            adjustment_working = slip1 > slip2
            passed = adjustment_working
            details = f"High difficulty slip: {slip1}, Low difficulty slip: {slip2}"
        else:
            details = f"Responses: {response1.status_code}, {response2.status_code}"
        
        self.log_test("Parameter Adjustment Logic", passed, details)
    
    def test_bloom_taxonomy_adjustments(self):
        """Test Bloom's taxonomy level adjustments"""
        # Test different Bloom levels by creating temporary metadata
        # This would normally be done through the metadata cache
        from ai_engine.src.knowledge_tracing.bkt.repository import QuestionMetadata
        
        # Test "Remember" level (should decrease guess rate)
        remember_metadata = QuestionMetadata(
            question_id="TEST_REMEMBER",
            difficulty_calibrated=0.5,
            bloom_level="Remember",
            estimated_time_seconds=60,
            required_process_skills=["memory"]
        )
        
        # Test "Create" level (should increase guess rate)
        create_metadata = QuestionMetadata(
            question_id="TEST_CREATE",
            difficulty_calibrated=0.5,
            bloom_level="Create",
            estimated_time_seconds=300,
            required_process_skills=["synthesis"]
        )
        
        # Get parameters with different Bloom levels
        remember_params = repository.get_parameters_with_context("test_concept", remember_metadata)
        create_params = repository.get_parameters_with_context("test_concept", create_metadata)
        
        # Create level should have higher guess rate than Remember level
        bloom_adjustment_working = create_params.guess_rate > remember_params.guess_rate
        
        self.log_test(
            "Bloom Taxonomy Adjustments",
            bloom_adjustment_working,
            f"Remember guess: {remember_params.guess_rate}, Create guess: {create_params.guess_rate}"
        )
    
    def run_all_tests(self):
        """Run all Phase 4A integration tests"""
        print("🧪 Running Phase 4A BKT Integration Tests...")
        print("=" * 60)
        
        # Reset repository state for clean testing
        repository.client.reset_data()
        
        self.test_health_check()
        self.test_question_metadata_retrieval()
        self.test_basic_parameter_retrieval()
        self.test_contextual_parameter_retrieval()
        self.test_knowledge_state_basic()
        self.test_bkt_update_without_context()
        self.test_bkt_update_with_context()
        self.test_parameter_adjustment_logic()
        self.test_bloom_taxonomy_adjustments()
        
        # Summary
        print("\n" + "=" * 60)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Phase 4A Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 All Phase 4A integration tests passed!")
            print("✅ Question metadata integration is working correctly")
            print("✅ Adaptive parameter calibration is functional")
            print("✅ BKT repository enhancements are verified")
        else:
            print("⚠️  Some tests failed - check implementation")
            failed_tests = [r for r in self.test_results if not r["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return passed_tests == total_tests


if __name__ == "__main__":
    tester = Phase4AAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)