#!/usr/bin/env python3
"""
Manual Supabase table setup using direct table operations
"""

import os
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_supabase_tables():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    logger.info("🚀 Setting up Supabase data...")
    
    # Insert initial BKT parameters
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
        }
    ]
    
    try:
        result = supabase.table('bkt_parameters').upsert(initial_params).execute()
        logger.info(f"✅ Seeded {len(result.data)} BKT parameter sets")
    except Exception as e:
        logger.error(f"❌ BKT parameters setup failed: {e}")
    
    # Insert sample question metadata
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
        }
    ]
    
    try:
        result = supabase.table('question_metadata_cache').upsert(sample_questions).execute()
        logger.info(f"✅ Seeded {len(result.data)} sample questions")
    except Exception as e:
        logger.error(f"❌ Question metadata setup failed: {e}")
    
    logger.info("🎉 Supabase data setup complete!")
    return True

if __name__ == "__main__":
    success = setup_supabase_tables()
    exit(0 if success else 1)