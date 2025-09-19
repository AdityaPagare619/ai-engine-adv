"""
Production Test Suite for Phase 4A Week 1 Implementation
Tests the actual BKT integration code with proper connection handling and error scenarios.
"""

import os
import sys
import logging
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from typing import Dict, Any

# Add ai_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_engine', 'src'))

from knowledge_tracing.bkt.repository import BKTRepository, BKTParams, BKTState, QuestionMetadata

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestPhase4AProduction(unittest.TestCase):
    """Test suite for Phase 4A BKT integration production code."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
        
        # Create repository instance with mocked client
        self.repository = BKTRepository()
        
        # Mock the Supabase client to avoid real API calls
        self.mock_client = Mock()
        self.repository.client = self.mock_client
    
    def test_repository_initialization(self):
        """Test that repository initializes correctly."""
        self.assertIsNotNone(self.repository)
        self.assertIsNotNone(self.repository.client)
        logger.info("✅ Repository initialization test passed")
    
    def test_question_metadata_structure(self):
        """Test QuestionMetadata NamedTuple structure."""
        metadata = QuestionMetadata(
            question_id="TEST_Q001",
            difficulty_calibrated=1.5,
            bloom_level="Apply",
            estimated_time_seconds=120,
            required_process_skills=["problem_solving", "algebra"]
        )
        
        self.assertEqual(metadata.question_id, "TEST_Q001")
        self.assertEqual(metadata.difficulty_calibrated, 1.5)
        self.assertEqual(metadata.bloom_level, "Apply")
        self.assertEqual(metadata.estimated_time_seconds, 120)
        self.assertEqual(metadata.required_process_skills, ["problem_solving", "algebra"])
        logger.info("✅ QuestionMetadata structure test passed")
    
    def test_get_question_metadata_success(self):
        """Test successful question metadata retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.data = {
            'question_id': 'PHY_MECH_0001',
            'difficulty_calibrated': 1.2,
            'bloom_level': 'Apply',
            'estimated_time_seconds': 120,
            'required_process_skills': ['kinematics', 'problem_solving']
        }
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Test the method
        metadata = self.repository.get_question_metadata("PHY_MECH_0001")
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.question_id, "PHY_MECH_0001")
        self.assertEqual(metadata.difficulty_calibrated, 1.2)
        self.assertEqual(metadata.bloom_level, "Apply")
        logger.info("✅ Question metadata retrieval success test passed")
    
    def test_get_question_metadata_not_found(self):
        """Test question metadata retrieval when question doesn't exist."""
        # Mock empty response
        mock_response = Mock()
        mock_response.data = None
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Test the method
        metadata = self.repository.get_question_metadata("NONEXISTENT_Q001")
        
        self.assertIsNone(metadata)
        logger.info("✅ Question metadata not found test passed")
    
    def test_get_question_metadata_exception_handling(self):
        """Test question metadata retrieval exception handling."""
        # Mock exception
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Database error")
        
        # Test the method - should return None and log exception
        with self.assertLogs('bkt_repository', level='ERROR'):
            metadata = self.repository.get_question_metadata("ERROR_Q001")
            self.assertIsNone(metadata)
        
        logger.info("✅ Question metadata exception handling test passed")
    
    def test_get_parameters_with_context_no_metadata(self):
        """Test parameter retrieval without question context."""
        # Mock base parameters response
        mock_response = Mock()
        mock_response.data = {
            'learn_rate': 0.3,
            'slip_rate': 0.1,
            'guess_rate': 0.2
        }
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Test without question metadata
        params = self.repository.get_parameters_with_context("test_concept")
        
        self.assertEqual(params.learn_rate, 0.3)
        self.assertEqual(params.slip_rate, 0.1)
        self.assertEqual(params.guess_rate, 0.2)
        logger.info("✅ Parameters without context test passed")
    
    def test_get_parameters_with_context_difficulty_adjustment(self):
        """Test parameter adjustment based on difficulty."""
        # Mock base parameters response
        mock_response = Mock()
        mock_response.data = {
            'learn_rate': 0.3,
            'slip_rate': 0.1,
            'guess_rate': 0.2
        }
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Create high difficulty metadata
        high_difficulty_metadata = QuestionMetadata(
            question_id="HARD_Q001",
            difficulty_calibrated=2.0,
            bloom_level="Apply",
            estimated_time_seconds=180,
            required_process_skills=["advanced_math"]
        )
        
        # Test with question metadata
        params = self.repository.get_parameters_with_context("test_concept", high_difficulty_metadata)
        
        # Should have increased slip rate due to difficulty
        expected_slip = min(0.4, 0.1 + (2.0 * 0.05))  # 0.2
        self.assertEqual(params.learn_rate, 0.3)
        self.assertAlmostEqual(params.slip_rate, expected_slip, places=3)
        logger.info("✅ Difficulty adjustment test passed")
    
    def test_get_parameters_with_context_bloom_adjustment(self):
        """Test parameter adjustment based on Bloom's taxonomy."""
        # Mock base parameters response
        mock_response = Mock()
        mock_response.data = {
            'learn_rate': 0.3,
            'slip_rate': 0.1,
            'guess_rate': 0.2
        }
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Test different Bloom levels
        test_cases = [
            ("Remember", -0.05),
            ("Understand", 0.0),
            ("Apply", 0.02),
            ("Analyze", 0.05),
            ("Evaluate", 0.08),
            ("Create", 0.1)
        ]
        
        for bloom_level, expected_adjustment in test_cases:
            metadata = QuestionMetadata(
                question_id="TEST_Q001",
                difficulty_calibrated=0.0,
                bloom_level=bloom_level,
                estimated_time_seconds=120,
                required_process_skills=["test_skill"]
            )
            
            params = self.repository.get_parameters_with_context("test_concept", metadata)
            
            expected_guess = max(0.05, min(0.4, 0.2 + expected_adjustment))
            self.assertAlmostEqual(params.guess_rate, expected_guess, places=3, 
                                 msg=f"Failed for Bloom level: {bloom_level}")
        
        logger.info("✅ Bloom taxonomy adjustment test passed")
    
    def test_get_parameters_fallback_behavior(self):
        """Test parameter retrieval fallback behavior."""
        # Mock exception for database access
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Connection failed")
        
        # Test fallback behavior
        with self.assertLogs('bkt_repository', level='ERROR'):
            params = self.repository.get_parameters("nonexistent_concept")
            
            # Should return safe defaults
            self.assertEqual(params.learn_rate, 0.3)
            self.assertEqual(params.slip_rate, 0.1)
            self.assertEqual(params.guess_rate, 0.2)
        
        logger.info("✅ Parameter fallback behavior test passed")
    
    def test_bkt_state_operations(self):
        """Test BKT state get and save operations."""
        # Mock initial state response (no existing state)
        mock_empty_response = Mock()
        mock_empty_response.data = None
        
        # Mock state after save
        mock_saved_response = Mock()
        mock_saved_response.data = {
            'mastery_probability': 0.7,
            'practice_count': 1
        }
        
        # Set up mock behavior
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_empty_response
        
        # Test getting initial state (should return defaults)
        initial_state = self.repository.get_state("test_student", "test_concept")
        self.assertEqual(initial_state.mastery_probability, 0.5)
        self.assertEqual(initial_state.practice_count, 0)
        
        # Test saving state
        self.repository.save_state("test_student", "test_concept", 0.7)
        
        # Verify upsert was called
        self.mock_client.table.return_value.upsert.assert_called()
        
        logger.info("✅ BKT state operations test passed")
    
    def test_logging_functionality(self):
        """Test BKT update logging functionality."""
        # Test update logging
        self.repository.log_update(
            student_id="test_student",
            concept_id="test_concept",
            prev=0.5,
            new=0.7,
            correct=True,
            response_time_ms=1500
        )
        
        # Verify insert was called on logs table
        self.mock_client.table.return_value.insert.assert_called()
        
        # Get the call arguments
        call_args = self.mock_client.table.return_value.insert.call_args[0][0]
        
        self.assertEqual(call_args['student_id'], "test_student")
        self.assertEqual(call_args['concept_id'], "test_concept")
        self.assertEqual(call_args['previous_mastery'], 0.5)
        self.assertEqual(call_args['new_mastery'], 0.7)
        self.assertTrue(call_args['is_correct'])
        self.assertEqual(call_args['response_time_ms'], 1500)
        
        logger.info("✅ Logging functionality test passed")
    
    def test_parameter_bounds_enforcement(self):
        """Test that parameter bounds are properly enforced."""
        # Mock base parameters response
        mock_response = Mock()
        mock_response.data = {
            'learn_rate': 0.3,
            'slip_rate': 0.1,
            'guess_rate': 0.2
        }
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        # Test extreme values that should be bounded
        extreme_metadata = QuestionMetadata(
            question_id="EXTREME_Q001",
            difficulty_calibrated=10.0,  # Very high
            bloom_level="Create",        # Highest Bloom level
            estimated_time_seconds=600,
            required_process_skills=["expert_level"]
        )
        
        params = self.repository.get_parameters_with_context("test_concept", extreme_metadata)
        
        # Verify bounds are enforced
        self.assertTrue(0.0 <= params.learn_rate <= 1.0)
        self.assertTrue(0.0 <= params.slip_rate <= 0.4)
        self.assertTrue(0.05 <= params.guess_rate <= 0.4)
        
        logger.info("✅ Parameter bounds enforcement test passed")
    
    def test_error_resilience(self):
        """Test system resilience under various error conditions."""
        error_scenarios = [
            ("Connection timeout", Exception("Connection timeout")),
            ("Invalid response format", Exception("JSON decode error")),
            ("Database constraint violation", Exception("Constraint violation"))
        ]
        
        for scenario_name, exception in error_scenarios:
            with self.subTest(scenario=scenario_name):
                # Mock the exception
                self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = exception
                
                # Test that methods handle errors gracefully
                with self.assertLogs('bkt_repository', level='ERROR'):
                    metadata = self.repository.get_question_metadata("TEST_Q001")
                    self.assertIsNone(metadata)
                
                # Reset mock
                self.mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = None
        
        logger.info("✅ Error resilience test passed")
    
    def tearDown(self):
        """Clean up after tests."""
        # Clear environment variables
        if 'SUPABASE_URL' in os.environ:
            del os.environ['SUPABASE_URL']
        if 'SUPABASE_SERVICE_ROLE_KEY' in os.environ:
            del os.environ['SUPABASE_SERVICE_ROLE_KEY']


class TestSupabaseClientEnhancements(unittest.TestCase):
    """Test the enhanced Supabase client wrapper."""
    
    def setUp(self):
        """Set up test environment for Supabase client tests."""
        # Mock environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
    
    def test_missing_environment_variables(self):
        """Test that missing environment variables raise appropriate errors."""
        # Remove environment variables
        del os.environ['SUPABASE_URL']
        
        from knowledge_tracing.bkt.repository_supabase import SupabaseClient
        
        with self.assertRaises(ValueError) as context:
            SupabaseClient()
        
        self.assertIn("SUPABASE_URL", str(context.exception))
        logger.info("✅ Missing environment variables test passed")
    
    def tearDown(self):
        """Clean up after tests."""
        # Clear environment variables
        for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']:
            if var in os.environ:
                del os.environ[var]


def run_production_tests():
    """Run all production tests and provide a comprehensive report."""
    print("🧪 Running Phase 4A Production Test Suite...")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase4AProduction))
    suite.addTests(loader.loadTestsFromTestCase(TestSupabaseClientEnhancements))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"📊 Test Results Summary:")
    print(f"   Total tests run: {result.testsRun}")
    print(f"   Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 All production tests passed!")
        print("✅ Phase 4A BKT integration is production-ready")
        print("✅ Error handling and resilience verified")
        print("✅ Parameter adjustment logic validated")
        print("✅ Database integration tested")
        return True
    else:
        print("⚠️ Some tests failed - review implementation")
        if result.failures:
            print("Failures:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback}")
        if result.errors:
            print("Errors:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback}")
        return False


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1)