"""
Tests for Phase 4A Week 1: BKT Integration with Question Metadata
Tests the enhanced repository with adaptive calibration based on question metadata.
"""

import pytest
import sys
import os
from unittest.mock import patch

# Add the parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from ai_engine.src.knowledge_tracing.bkt.repository import (
    BKTRepository, 
    BKTParams, 
    BKTState, 
    QuestionMetadata
)
from ai_engine.src.knowledge_tracing.bkt.tests.mock_supabase import MockSupabaseClient


class TestPhase4AIntegration:
    
    @pytest.fixture
    def mock_repository(self):
        """Create repository with mock Supabase client"""
        mock_client = MockSupabaseClient()
        repo = BKTRepository()
        repo.client = mock_client  # Replace with mock
        return repo, mock_client
    
    def test_get_question_metadata_success(self, mock_repository):
        """Test successful retrieval of question metadata"""
        repo, mock_client = mock_repository
        
        # Test fetching existing question metadata
        metadata = repo.get_question_metadata("PHY_MECH_0001")
        
        assert metadata is not None
        assert metadata.question_id == "PHY_MECH_0001"
        assert metadata.difficulty_calibrated == 1.2
        assert metadata.bloom_level == "Apply"
        assert metadata.estimated_time_seconds == 120
        assert metadata.required_process_skills == ["kinematics", "problem_solving"]
    
    def test_get_question_metadata_not_found(self, mock_repository):
        """Test retrieval of non-existent question metadata"""
        repo, mock_client = mock_repository
        
        # Test fetching non-existent question
        metadata = repo.get_question_metadata("NONEXISTENT_Q001")
        assert metadata is None
    
    def test_get_parameters_with_context_no_metadata(self, mock_repository):
        """Test parameter retrieval without question context"""
        repo, mock_client = mock_repository
        
        # Test base parameters without question context
        params = repo.get_parameters_with_context("test_concept")
        
        # Should return base parameters
        assert params.learn_rate == 0.3
        assert params.slip_rate == 0.1
        assert params.guess_rate == 0.2
    
    def test_get_parameters_with_context_difficulty_adjustment(self, mock_repository):
        """Test parameter adjustment based on question difficulty"""
        repo, mock_client = mock_repository
        
        # Create question metadata with high difficulty
        metadata = QuestionMetadata(
            question_id="HARD_Q001",
            difficulty_calibrated=2.0,  # High difficulty
            bloom_level="Apply",
            estimated_time_seconds=180,
            required_process_skills=["advanced_physics"]
        )
        
        params = repo.get_parameters_with_context("test_concept", metadata)
        
        # Should have adjusted slip rate (higher for harder questions)
        assert params.learn_rate == 0.3  # Unchanged
        assert params.slip_rate > 0.1    # Increased due to difficulty
        assert params.slip_rate <= 0.4   # Bounded
        
        # Calculate expected adjustment: base (0.1) + (difficulty * 0.05) = 0.1 + (2.0 * 0.05) = 0.2
        expected_slip = min(0.4, 0.1 + (2.0 * 0.05))
        assert abs(params.slip_rate - expected_slip) < 0.001
    
    def test_get_parameters_with_context_bloom_adjustment(self, mock_repository):
        """Test parameter adjustment based on Bloom's taxonomy level"""
        repo, mock_client = mock_repository
        
        # Test different Bloom levels
        bloom_levels = [
            ("Remember", -0.05),
            ("Understand", 0.0),
            ("Apply", 0.02),
            ("Analyze", 0.05),
            ("Evaluate", 0.08),
            ("Create", 0.1)
        ]
        
        for bloom_level, expected_adjustment in bloom_levels:
            metadata = QuestionMetadata(
                question_id="TEST_Q001",
                difficulty_calibrated=0.0,  # No difficulty adjustment
                bloom_level=bloom_level,
                estimated_time_seconds=120,
                required_process_skills=["test_skill"]
            )
            
            params = repo.get_parameters_with_context("test_concept", metadata)
            
            # Base guess rate (0.2) + bloom adjustment
            expected_guess = max(0.05, min(0.4, 0.2 + expected_adjustment))
            assert abs(params.guess_rate - expected_guess) < 0.001, f"Failed for {bloom_level}"
    
    def test_get_parameters_with_context_combined_adjustments(self, mock_repository):
        """Test combined difficulty and Bloom level adjustments"""
        repo, mock_client = mock_repository
        
        metadata = QuestionMetadata(
            question_id="COMPLEX_Q001",
            difficulty_calibrated=1.5,    # High difficulty
            bloom_level="Create",         # Highest Bloom level
            estimated_time_seconds=300,
            required_process_skills=["complex_reasoning"]
        )
        
        params = repo.get_parameters_with_context("test_concept", metadata)
        
        # Check both adjustments applied
        expected_slip = min(0.4, 0.1 + (1.5 * 0.05))  # 0.175
        expected_guess = max(0.05, min(0.4, 0.2 + 0.1))  # 0.3
        
        assert abs(params.slip_rate - expected_slip) < 0.001
        assert abs(params.guess_rate - expected_guess) < 0.001
        assert params.learn_rate == 0.3  # Unchanged
    
    def test_get_parameters_with_context_bounds(self, mock_repository):
        """Test parameter bounds are respected"""
        repo, mock_client = mock_repository
        
        # Test extreme values
        metadata = QuestionMetadata(
            question_id="EXTREME_Q001",
            difficulty_calibrated=10.0,   # Very high difficulty
            bloom_level="Create",         # Highest Bloom level
            estimated_time_seconds=600,
            required_process_skills=["expert_level"]
        )
        
        params = repo.get_parameters_with_context("test_concept", metadata)
        
        # All parameters should be within bounds
        assert 0.0 <= params.learn_rate <= 1.0
        assert 0.0 <= params.slip_rate <= 0.4    # Bounded max
        assert 0.05 <= params.guess_rate <= 0.4  # Bounded min and max
    
    def test_get_parameters_with_context_invalid_difficulty(self, mock_repository):
        """Test handling of invalid difficulty values"""
        repo, mock_client = mock_repository
        
        # Test with None difficulty
        metadata = QuestionMetadata(
            question_id="NULL_DIFF_Q001",
            difficulty_calibrated=None,
            bloom_level="Apply",
            estimated_time_seconds=120,
            required_process_skills=["test_skill"]
        )
        
        params = repo.get_parameters_with_context("test_concept", metadata)
        
        # Should only apply Bloom adjustment, not difficulty
        expected_guess = max(0.05, min(0.4, 0.2 + 0.02))  # Only Bloom adjustment
        assert abs(params.guess_rate - expected_guess) < 0.001
        assert params.slip_rate == 0.1  # No difficulty adjustment
    
    def test_get_parameters_with_context_unknown_bloom(self, mock_repository):
        """Test handling of unknown Bloom levels"""
        repo, mock_client = mock_repository
        
        metadata = QuestionMetadata(
            question_id="UNKNOWN_BLOOM_Q001",
            difficulty_calibrated=1.0,
            bloom_level="UnknownLevel",  # Not in our mapping
            estimated_time_seconds=120,
            required_process_skills=["test_skill"]
        )
        
        params = repo.get_parameters_with_context("test_concept", metadata)
        
        # Should apply difficulty adjustment but no Bloom adjustment
        expected_slip = min(0.4, 0.1 + (1.0 * 0.05))  # 0.15
        expected_guess = 0.2  # No Bloom adjustment
        
        assert abs(params.slip_rate - expected_slip) < 0.001
        assert params.guess_rate == expected_guess
    
    def test_repository_integration(self, mock_repository):
        """Test full integration of enhanced repository"""
        repo, mock_client = mock_repository
        
        # Test complete workflow
        student_id = "test-student-001"
        concept_id = "kinematics_basic"
        question_id = "PHY_MECH_0001"
        
        # 1. Get question metadata
        metadata = repo.get_question_metadata(question_id)
        assert metadata is not None
        
        # 2. Get contextual parameters
        params = repo.get_parameters_with_context(concept_id, metadata)
        assert isinstance(params, BKTParams)
        
        # 3. Get initial state
        state = repo.get_state(student_id, concept_id)
        assert state.mastery_probability == 0.5  # Default
        assert state.practice_count == 0
        
        # 4. Save updated state
        new_mastery = 0.7
        repo.save_state(student_id, concept_id, new_mastery)
        
        # 5. Verify state updated
        updated_state = repo.get_state(student_id, concept_id)
        assert updated_state.mastery_probability == new_mastery
        assert updated_state.practice_count == 1
        
        # 6. Log the update
        repo.log_update(
            student_id=student_id,
            concept_id=concept_id,
            prev=0.5,
            new=new_mastery,
            correct=True,
            response_time_ms=2500
        )
        
        # Verify log entry
        logs = mock_client.get_data("bkt_update_logs")
        assert len(logs) == 1
        assert logs[0]["student_id"] == student_id
        assert logs[0]["concept_id"] == concept_id
        assert logs[0]["previous_mastery"] == 0.5
        assert logs[0]["new_mastery"] == new_mastery
        assert logs[0]["is_correct"] == True
        assert logs[0]["response_time_ms"] == 2500
    
    def test_error_handling(self, mock_repository):
        """Test error handling and fallbacks"""
        repo, mock_client = mock_repository
        
        # Test with concept that doesn't exist
        params = repo.get_parameters("nonexistent_concept")
        
        # Should return safe defaults
        assert params.learn_rate == 0.3
        assert params.slip_rate == 0.1
        assert params.guess_rate == 0.2
    
    @patch('ai_engine.src.knowledge_tracing.bkt.repository.logger')
    def test_exception_logging(self, mock_logger, mock_repository):
        """Test that exceptions are properly logged"""
        repo, mock_client = mock_repository
        
        # Force an exception by breaking the mock client
        mock_client.data_store = None
        
        # This should handle the exception gracefully
        metadata = repo.get_question_metadata("PHY_MECH_0001")
        assert metadata is None
        
        # Verify exception was logged
        mock_logger.exception.assert_called()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])