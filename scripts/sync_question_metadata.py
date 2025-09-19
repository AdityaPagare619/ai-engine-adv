#!/usr/bin/env python3
"""
Question Metadata Sync Script for Phase 4A Week 1
Reads from PostgreSQL canonical questions table and syncs to Supabase cache
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import hashlib
import json
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionMetadataSync:
    def __init__(self):
        # PostgreSQL connection (source of truth)
        self.postgres_url = os.getenv('POSTGRES_URL', 'postgresql://jee_admin:secure_jee_2025@localhost:5432/jee_smart_platform')
        
        # Supabase connection (cache destination)
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Sync tracking
        self.sync_batch_size = int(os.getenv('SYNC_BATCH_SIZE', '100'))
        self.sync_state_table = 'question_metadata_sync_state'
        
    def fetch_questions_from_postgres(self, incremental: bool = True, last_sync_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch question metadata from PostgreSQL with optional incremental sync."""
        try:
            conn = psycopg2.connect(self.postgres_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            
            # Base query for enhanced questions table with all metadata fields
            base_query = """
            SELECT 
                question_id,
                subject,
                topic,
                difficulty_calibrated,
                bloom_level,
                estimated_time_seconds,
                required_process_skills,
                required_formulas,
                question_type,
                marks,
                status,
                content_hash,
                updated_at,
                created_at
            FROM questions 
            WHERE status IN ('released', 'beta')
            AND question_id IS NOT NULL
            """
            
            # Add incremental sync condition if requested
            if incremental and last_sync_time:
                query = base_query + " AND updated_at > %s ORDER BY updated_at DESC"
                cursor.execute(query, (last_sync_time,))
                logger.info(f"Performing incremental sync since {last_sync_time}")
            else:
                query = base_query + " ORDER BY updated_at DESC"
                cursor.execute(query)
                logger.info("Performing full sync")
            
            questions = []
            for row in cursor.fetchall():
                question_data = dict(row)
                
                # Convert PostgreSQL arrays to Python lists for JSON serialization
                if question_data.get('required_process_skills'):
                    question_data['required_process_skills'] = list(question_data['required_process_skills'])
                else:
                    question_data['required_process_skills'] = []
                    
                if question_data.get('required_formulas'):
                    question_data['required_formulas'] = list(question_data['required_formulas'])
                else:
                    question_data['required_formulas'] = []
                
                # Ensure timestamps are timezone-aware
                if question_data.get('updated_at') and question_data['updated_at'].tzinfo is None:
                    question_data['updated_at'] = question_data['updated_at'].replace(tzinfo=timezone.utc)
                if question_data.get('created_at') and question_data['created_at'].tzinfo is None:
                    question_data['created_at'] = question_data['created_at'].replace(tzinfo=timezone.utc)
                
                questions.append(question_data)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Fetched {len(questions)} questions from PostgreSQL")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to fetch questions from PostgreSQL: {e}")
            raise
    
    def sync_to_supabase(self, questions: List[Dict[str, Any]]) -> int:
        """Sync question metadata to Supabase cache"""
        try:
            synced_count = 0
            
            for question in questions:
                # Prepare data for cache
                cache_data = {
                    'question_id': question['question_id'],
                    'subject': question['subject'],
                    'topic': question['topic'],
                    'difficulty_calibrated': question['difficulty_calibrated'],
                    'bloom_level': question['bloom_level'],
                    'estimated_time_seconds': question['estimated_time_seconds'],
                    'required_process_skills': question['required_process_skills'],
                    'required_formulas': question['required_formulas'],
                    'question_type': question['question_type'],
                    'marks': question['marks'],
                    'status': question['status'],
                    'content_hash': question['content_hash'],
                    'last_synced_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Upsert to cache (insert or update)
                result = self.supabase.table('question_metadata_cache').upsert(cache_data).execute()
                
                if result.data:
                    synced_count += 1
                    if synced_count % 10 == 0:
                        logger.info(f"Synced {synced_count} questions...")
                        
            logger.info(f"Successfully synced {synced_count} questions to Supabase cache")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync questions to Supabase: {e}")
            raise
    
    def verify_sync(self) -> Dict[str, int]:
        """Verify the sync by comparing counts"""
        try:
            # Count in PostgreSQL
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE status IN ('released', 'beta')")
            postgres_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            # Count in Supabase cache
            cache_result = self.supabase.table('question_metadata_cache').select('question_id', count='exact').execute()
            cache_count = cache_result.count if cache_result.count is not None else 0
            
            verification = {
                'postgres_count': postgres_count,
                'cache_count': cache_count,
                'sync_success': postgres_count == cache_count
            }
            
            logger.info(f"Verification - PostgreSQL: {postgres_count}, Cache: {cache_count}")
            
            return verification
            
        except Exception as e:
            logger.error(f"Failed to verify sync: {e}")
            return {'postgres_count': 0, 'cache_count': 0, 'sync_success': False}
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the timestamp of the last successful sync."""
        try:
            result = self.supabase.table(self.sync_state_table).select('last_sync_time').order('last_sync_time', desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                last_sync_str = result.data[0]['last_sync_time']
                return datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not retrieve last sync time: {e}")
            return None
    
    def update_sync_state(self, sync_time: datetime, questions_synced: int, success: bool) -> None:
        """Update the sync state tracking table."""
        try:
            sync_record = {
                'sync_timestamp': sync_time.isoformat(),
                'questions_synced': questions_synced,
                'success': success,
                'last_sync_time': sync_time.isoformat()
            }
            
            self.supabase.table(self.sync_state_table).insert(sync_record).execute()
            logger.info(f"Updated sync state: {questions_synced} questions, success: {success}")
            
        except Exception as e:
            logger.warning(f"Could not update sync state: {e}")
    
    def sync_to_supabase_batch(self, questions: List[Dict[str, Any]]) -> int:
        """Sync questions to Supabase in batches with better error handling."""
        try:
            synced_count = 0
            failed_questions = []
            
            # Process in batches
            for i in range(0, len(questions), self.sync_batch_size):
                batch = questions[i:i + self.sync_batch_size]
                batch_num = (i // self.sync_batch_size) + 1
                total_batches = (len(questions) + self.sync_batch_size - 1) // self.sync_batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")
                
                try:
                    # Prepare batch data
                    cache_batch = []
                    for question in batch:
                        cache_data = {
                            'question_id': question['question_id'],
                            'subject': question.get('subject'),
                            'topic': question.get('topic'),
                            'difficulty_calibrated': question.get('difficulty_calibrated'),
                            'bloom_level': question.get('bloom_level'),
                            'estimated_time_seconds': question.get('estimated_time_seconds'),
                            'required_process_skills': question.get('required_process_skills', []),
                            'required_formulas': question.get('required_formulas', []),
                            'question_type': question.get('question_type'),
                            'marks': question.get('marks'),
                            'status': question.get('status'),
                            'content_hash': question.get('content_hash'),
                            'last_synced': datetime.utcnow().isoformat(),
                            'updated_at': question.get('updated_at', datetime.utcnow()).isoformat() if isinstance(question.get('updated_at'), datetime) else question.get('updated_at')
                        }
                        cache_batch.append(cache_data)
                    
                    # Upsert batch
                    result = self.supabase.table('question_metadata_cache').upsert(cache_batch).execute()
                    
                    if result.data:
                        batch_synced = len(result.data)
                        synced_count += batch_synced
                        logger.info(f"Batch {batch_num} completed: {batch_synced} questions synced")
                    
                    # Brief pause between batches to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as batch_error:
                    logger.error(f"Batch {batch_num} failed: {batch_error}")
                    
                    # Try individual upserts for failed batch
                    for question in batch:
                        try:
                            cache_data = {
                                'question_id': question['question_id'],
                                'subject': question.get('subject'),
                                'topic': question.get('topic'),
                                'difficulty_calibrated': question.get('difficulty_calibrated'),
                                'bloom_level': question.get('bloom_level'),
                                'estimated_time_seconds': question.get('estimated_time_seconds'),
                                'required_process_skills': question.get('required_process_skills', []),
                                'question_type': question.get('question_type'),
                                'last_synced': datetime.utcnow().isoformat(),
                                'updated_at': datetime.utcnow().isoformat()
                            }
                            
                            self.supabase.table('question_metadata_cache').upsert(cache_data).execute()
                            synced_count += 1
                            
                        except Exception as individual_error:
                            logger.error(f"Failed to sync question {question.get('question_id', 'unknown')}: {individual_error}")
                            failed_questions.append(question['question_id'])
            
            if failed_questions:
                logger.warning(f"Failed to sync {len(failed_questions)} questions: {failed_questions[:10]}{'...' if len(failed_questions) > 10 else ''}")
            
            logger.info(f"Successfully synced {synced_count} questions to Supabase cache")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync questions to Supabase: {e}")
            raise
    
    def run_sync(self, force_full_sync: bool = False) -> bool:
        """Run the complete sync process with incremental sync support."""
        sync_start_time = datetime.utcnow()
        
        try:
            logger.info("🚀 Starting question metadata sync...")
            
            # Determine sync type
            last_sync_time = None if force_full_sync else self.get_last_sync_time()
            
            if last_sync_time:
                logger.info(f"📅 Last sync: {last_sync_time} - performing incremental sync")
            else:
                logger.info("🔄 Performing full sync")
            
            # Fetch from PostgreSQL
            questions = self.fetch_questions_from_postgres(incremental=not force_full_sync, last_sync_time=last_sync_time)
            
            if not questions:
                logger.info("✅ No new questions to sync")
                self.update_sync_state(sync_start_time, 0, True)
                return True
            
            # Sync to Supabase using batch processing
            synced_count = self.sync_to_supabase_batch(questions)
            
            # Verify sync only for full syncs or if requested
            verification = {'sync_success': True}  # Skip verification for incremental syncs by default
            
            if force_full_sync or len(questions) > 100:  # Verify for large syncs
                logger.info("🔍 Verifying sync...")
                verification = self.verify_sync()
            
            # Update sync state
            sync_success = verification['sync_success'] and synced_count > 0
            self.update_sync_state(sync_start_time, synced_count, sync_success)
            
            if sync_success:
                logger.info(f"✅ Question metadata sync completed successfully! ({synced_count} questions)")
                return True
            else:
                logger.warning(f"⚠️ Sync completed with issues - {synced_count} questions synced")
                return False
                
        except Exception as e:
            logger.error(f"❌ Question metadata sync failed: {e}")
            self.update_sync_state(sync_start_time, 0, False)
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync question metadata from PostgreSQL to Supabase")
    parser.add_argument('--full', action='store_true', help='Force full sync instead of incremental')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for sync operations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        sync = QuestionMetadataSync()
        
        # Override batch size if provided
        if args.batch_size != 100:
            sync.sync_batch_size = args.batch_size
            logger.info(f"Using batch size: {args.batch_size}")
        
        success = sync.run_sync(force_full_sync=args.full)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()