#!/usr/bin/env python3
"""
Setup Supabase tables for BKT system
Creates all necessary tables in your Supabase instance
"""

import os
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_supabase_tables():
    """Create all BKT tables in Supabase"""
    
    # Get Supabase connection
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    logger.info("🚀 Setting up Supabase tables...")
    
    # Create tables using SQL
    tables_sql = """
    -- BKT Parameters table
    CREATE TABLE IF NOT EXISTS bkt_parameters (
      concept_id VARCHAR(100) PRIMARY KEY,
      learn_rate NUMERIC(5,4) NOT NULL CHECK (learn_rate BETWEEN 0 AND 1),
      slip_rate NUMERIC(5,4) NOT NULL CHECK (slip_rate BETWEEN 0 AND 0.5),
      guess_rate NUMERIC(5,4) NOT NULL CHECK (guess_rate BETWEEN 0 AND 0.5),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      engine_version TEXT DEFAULT 'bkt_1.0'
    );

    -- BKT Knowledge States table
    CREATE TABLE IF NOT EXISTS bkt_knowledge_states (
      student_id VARCHAR(100) NOT NULL,
      concept_id VARCHAR(100) NOT NULL,
      mastery_probability NUMERIC(5,4) NOT NULL CHECK (mastery_probability BETWEEN 0 AND 1),
      practice_count INTEGER NOT NULL DEFAULT 0 CHECK (practice_count >= 0),
      last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      confidence_interval_lower NUMERIC(5,4),
      confidence_interval_upper NUMERIC(5,4),
      PRIMARY KEY (student_id, concept_id)
    );

    -- BKT Update Logs table
    CREATE TABLE IF NOT EXISTS bkt_update_logs (
      id SERIAL PRIMARY KEY,
      student_id VARCHAR(100) NOT NULL,
      concept_id VARCHAR(100) NOT NULL,
      question_id VARCHAR(250),
      previous_mastery NUMERIC(5,4) NOT NULL,
      new_mastery NUMERIC(5,4) NOT NULL,
      is_correct BOOLEAN NOT NULL,
      response_time_ms INTEGER,
      timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      params_used JSONB DEFAULT '{}',
      engine_version TEXT DEFAULT 'bkt_1.0'
    );

    -- Question Metadata Cache for fast lookups
    CREATE TABLE IF NOT EXISTS question_metadata_cache (
      question_id VARCHAR(250) PRIMARY KEY,
      subject VARCHAR(20),
      topic TEXT,
      difficulty_calibrated NUMERIC(5,3),
      bloom_level VARCHAR(20),
      estimated_time_seconds INTEGER,
      required_process_skills TEXT[],
      required_formulas TEXT[],
      question_type VARCHAR(30),
      marks NUMERIC(4,2),
      status VARCHAR(20),
      content_hash TEXT,
      last_synced TIMESTAMPTZ DEFAULT NOW(),
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Sync State Tracking
    CREATE TABLE IF NOT EXISTS question_metadata_sync_state (
      id SERIAL PRIMARY KEY,
      sync_timestamp TIMESTAMPTZ NOT NULL,
      questions_synced INTEGER NOT NULL,
      success BOOLEAN NOT NULL,
      last_sync_time TIMESTAMPTZ NOT NULL
    );

    -- BKT Evaluation Windows
    CREATE TABLE IF NOT EXISTS bkt_evaluation_windows (
      id SERIAL PRIMARY KEY,
      concept_id VARCHAR(100),
      start_timestamp TIMESTAMPTZ NOT NULL,
      end_timestamp TIMESTAMPTZ NOT NULL,
      next_step_auc NUMERIC(6,4),
      next_step_accuracy NUMERIC(6,4),
      brier_score NUMERIC(6,4),
      calibration_error NUMERIC(6,4),
      trajectory_validity NUMERIC(6,4),
      recommendation TEXT,
      evaluated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Selection Feedback for bandit optimization
    CREATE TABLE IF NOT EXISTS bkt_selection_feedback (
      id SERIAL PRIMARY KEY,
      student_id VARCHAR(100) NOT NULL,
      question_id VARCHAR(250) NOT NULL,
      selection_timestamp TIMESTAMPTZ NOT NULL,
      predicted_difficulty NUMERIC(5,3),
      predicted_correctness NUMERIC(5,4),
      actual_correct BOOLEAN,
      actual_response_time_ms INTEGER,
      reward NUMERIC(6,4),
      bandit_context JSONB,
      feedback_timestamp TIMESTAMPTZ DEFAULT NOW()
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_bkt_states_student ON bkt_knowledge_states(student_id);
    CREATE INDEX IF NOT EXISTS idx_bkt_states_concept ON bkt_knowledge_states(concept_id);
    CREATE INDEX IF NOT EXISTS idx_bkt_logs_timestamp ON bkt_update_logs(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_bkt_logs_student_concept ON bkt_update_logs(student_id, concept_id);
    CREATE INDEX IF NOT EXISTS idx_question_cache_lookup ON question_metadata_cache(question_id);
    CREATE INDEX IF NOT EXISTS idx_question_cache_difficulty ON question_metadata_cache(difficulty_calibrated);
    CREATE INDEX IF NOT EXISTS idx_question_cache_topic ON question_metadata_cache(subject, topic);
    """
    
    try:
        # Execute SQL using supabase client
        result = supabase.rpc('run_sql', {'query': tables_sql}).execute()
        logger.info("✅ Tables created successfully!")
        
        # Seed initial BKT parameters
        initial_params = [
            {
                'concept_id': 'kinematics_basic',
                'learn_rate': 0.25,
                'slip_rate': 0.10,
                'guess_rate': 0.20
            },
            {
                'concept_id': 'thermodynamics_basic',
                'learn_rate': 0.22,
                'slip_rate': 0.12,
                'guess_rate': 0.18
            },
            {
                'concept_id': 'organic_chemistry_basic',
                'learn_rate': 0.28,
                'slip_rate': 0.08,
                'guess_rate': 0.22
            },
            {
                'concept_id': 'calculus_limits',
                'learn_rate': 0.30,
                'slip_rate': 0.15,
                'guess_rate': 0.16
            },
            {
                'concept_id': 'algebra_quadratic',
                'learn_rate': 0.35,
                'slip_rate': 0.09,
                'guess_rate': 0.25
            }
        ]
        
        # Insert initial parameters
        try:
            result = supabase.table('bkt_parameters').insert(initial_params).execute()
            logger.info(f"✅ Seeded {len(initial_params)} BKT parameter sets")
        except Exception as e:
            logger.info("📝 BKT parameters already exist or insertion failed - continuing...")
        
        # Seed some sample question metadata
        sample_questions = [
            {
                'question_id': 'PHY_MECH_0001',
                'subject': 'Physics',
                'topic': 'Kinematics',
                'difficulty_calibrated': 1.2,
                'bloom_level': 'Apply',
                'estimated_time_seconds': 120,
                'required_process_skills': ['kinematics', 'problem_solving'],
                'question_type': 'MCQ',
                'marks': 4.0,
                'status': 'released'
            },
            {
                'question_id': 'CHEM_ORG_0001',
                'subject': 'Chemistry',
                'topic': 'Organic Chemistry',
                'difficulty_calibrated': 0.8,
                'bloom_level': 'Understand',
                'estimated_time_seconds': 90,
                'required_process_skills': ['organic_reactions', 'nomenclature'],
                'question_type': 'MCQ',
                'marks': 4.0,
                'status': 'released'
            },
            {
                'question_id': 'MATH_CALC_0001',
                'subject': 'Mathematics',
                'topic': 'Calculus',
                'difficulty_calibrated': 1.5,
                'bloom_level': 'Analyze',
                'estimated_time_seconds': 180,
                'required_process_skills': ['integration', 'differentiation'],
                'question_type': 'NUMERICAL',
                'marks': 4.0,
                'status': 'released'
            }
        ]
        
        try:
            result = supabase.table('question_metadata_cache').insert(sample_questions).execute()
            logger.info(f"✅ Seeded {len(sample_questions)} sample questions")
        except Exception as e:
            logger.info("📝 Sample questions already exist or insertion failed - continuing...")
        
        logger.info("🎉 Supabase setup complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Supabase tables: {e}")
        return False

if __name__ == "__main__":
    success = setup_supabase_tables()
    exit(0 if success else 1)