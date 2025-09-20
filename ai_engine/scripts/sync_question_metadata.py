# ai_engine/scripts/sync_question_metadata.py
"""
Sync canonical question metadata from Phase 1-3 Postgres into Supabase question_metadata_cache.
Environment:
  - POSTGRES_URL: e.g. postgres://user:pass@host:5432/db
  - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
  - SOURCE_TABLE (optional): defaults to 'question_bank'
  - BATCH_SIZE (optional): defaults to 500
This script is idempotent and safe to run repeatedly.
"""
import os
import json
import math
import time
import logging
from typing import List, Dict, Any, Iterator, Optional

import psycopg2
import psycopg2.extras
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_question_metadata")

SOURCE_TABLE = os.getenv("SOURCE_TABLE", "question_bank")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))

def connect_postgres():
    url = os.getenv("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL not set")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    return conn

def connect_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    return create_client(url, key)

def fetch_rows(conn) -> Iterator[Dict[str, Any]]:
    """
    Read required fields from source.
    Adjust column names to match your Phase 1-3 schema if different.
    """
    cols = [
        "question_id",
        "difficulty_calibrated",
        "bloom_level",
        "estimated_time_seconds",
        "required_process_skills",
        "question_type",
        "subject",
        "topic",
        "updated_at",
    ]
    sql = f"""
        SELECT {", ".join(cols)}
        FROM {SOURCE_TABLE}
        WHERE question_id IS NOT NULL
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        for row in cur:
            yield dict(row)

def chunk(iterable: List[Dict[str, Any]], size: int) -> Iterator[List[Dict[str, Any]]]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map source row → cache schema with safe defaults and length limits.
    """
    qid = str(row.get("question_id", "")).strip()[:250]
    required_skills = row.get("required_process_skills")
    if isinstance(required_skills, str):
        # Try JSON parse, else wrap as single
        try:
            required_skills = json.loads(required_skills)
        except Exception:
            required_skills = [required_skills]
    if required_skills is None:
        required_skills = []

    return {
        "question_id": qid,
        "subject": (row.get("subject") or None),
        "topic": (row.get("topic") or None),
        "difficulty_calibrated": row.get("difficulty_calibrated"),
        "bloom_level": (row.get("bloom_level") or None),
        "estimated_time_seconds": row.get("estimated_time_seconds"),
        "required_process_skills": required_skills,
        "question_type": (str(row.get("question_type") or "")[:30]),
        "last_synced": None,  # let DB defaults set this
    }

def main():
    pg = connect_postgres()
    sb = connect_supabase()
    table = sb.table("question_metadata_cache")

    logger.info("Fetching source rows...")
    rows = list(fetch_rows(pg))
    logger.info(f"Fetched {len(rows)} rows from {SOURCE_TABLE}")

    if not rows:
        logger.info("No rows to sync. Exiting.")
        return

    logger.info("Normalizing rows...")
    payload = [normalize_row(r) for r in rows]

    logger.info("Upserting into Supabase cache...")
    total = len(payload)
    for i, batch in enumerate(chunk(payload, BATCH_SIZE), start=1):
        table.upsert(batch).execute()
        logger.info(f"Upserted batch {i} ({len(batch)} rows). Progress: {min(i*BATCH_SIZE, total)}/{total}")

    logger.info("Sync complete.")

if __name__ == "__main__":
    main()
