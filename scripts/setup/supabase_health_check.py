#!/usr/bin/env python3
"""
Supabase health check and table inspection.
- Loads credentials from ai_engine/.env or project .env via python-dotenv.
- Verifies connection and probes expected tables.
- Prints row counts and up to 3 sample rows (safe fields only).
"""
import os
import json
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
    def find_dotenv(*args, **kwargs):  # type: ignore
        return ""
from supabase import create_client

EXPECTED_TABLES = [
    "bkt_parameters",
    "bkt_knowledge_states",
    "bkt_update_logs",
    "question_metadata_cache",
]

SAFE_FIELDS = {
    "bkt_parameters": ["concept_id", "learn_rate", "slip_rate", "guess_rate"],
    "bkt_knowledge_states": ["student_id", "concept_id", "mastery_probability", "practice_count"],
    "bkt_update_logs": ["student_id", "concept_id", "previous_mastery", "new_mastery", "is_correct", "timestamp"],
    "question_metadata_cache": ["question_id", "difficulty_calibrated", "bloom_level", "estimated_time_seconds"],
}


def _parse_env_file(path: str):
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip(); v = v.strip().strip('"')
                    if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") and not os.getenv(k):
                        os.environ[k] = v
    except Exception:
        pass

def load_env():
    # Load ai_engine/.env first, then fallback to project .env
    ai_env = os.path.join(os.path.dirname(__file__), "..", "..", "ai_engine", ".env")
    _parse_env_file(ai_env)
    # Try python-dotenv if available
    load_dotenv(ai_env, override=False)
    env_file = find_dotenv(usecwd=True)
    if env_file:
        _parse_env_file(env_file)
        load_dotenv(env_file, override=False)


def main():
    load_env()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env files.")
        raise SystemExit(1)

    client = create_client(url, key)

    print("Supabase connection: OK")

    for table in EXPECTED_TABLES:
        try:
            # Count rows via select and len (PostgREST may not support count(*) without head request)
            data = client.table(table).select("*").limit(3).execute().data
            total = client.table(table).select("*").execute().data
            count = len(total) if isinstance(total, list) else (1 if total else 0)

            # Prepare safe sample
            fields = SAFE_FIELDS.get(table)
            samples = []
            for row in (data or []):
                if fields:
                    samples.append({k: row.get(k) for k in fields})
                else:
                    samples.append(row)

            print(json.dumps({
                "table": table,
                "row_count": count,
                "sample": samples,
            }, indent=2))
        except Exception as e:
            print(json.dumps({
                "table": table,
                "error": str(e),
            }, indent=2))


if __name__ == "__main__":
    main()
