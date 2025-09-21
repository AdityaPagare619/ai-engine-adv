#!/usr/bin/env python3
"""
Seed minimal Supabase data required by the AI engine.
- Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from ai_engine/.env or project .env
- Inserts rows only if the target tables are empty or the concept/question IDs are missing.
"""
import os
import time
import json
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
    def find_dotenv(*args, **kwargs):  # type: ignore
        return ""
from supabase import create_client

SEED_PARAMS = [
    {"concept_id": "kinematics_basic", "learn_rate": 0.3, "slip_rate": 0.1, "guess_rate": 0.2},
    {"concept_id": "algebra_quadratics", "learn_rate": 0.25, "slip_rate": 0.12, "guess_rate": 0.22},
    {"concept_id": "thermodynamics_basic", "learn_rate": 0.28, "slip_rate": 0.1, "guess_rate": 0.2},
]

SEED_QUESTIONS = [
    {"question_id": "PHY_MECH_0001", "difficulty_calibrated": 1.2, "bloom_level": "Apply", "estimated_time_seconds": 120},
    {"question_id": "MATH_CALC_0001", "difficulty_calibrated": 0.8, "bloom_level": "Understand", "estimated_time_seconds": 90},
]


def load_env():
    ai_env = os.path.join(os.path.dirname(__file__), "..", "..", "ai_engine", ".env")
    if os.path.exists(ai_env):
        load_dotenv(ai_env, override=False)
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)


def ensure_bkt_parameters(client):
    existing = client.table("bkt_parameters").select("concept_id").execute().data or []
    existing_ids = {row.get("concept_id") for row in existing}
    to_insert = [row for row in SEED_PARAMS if row["concept_id"] not in existing_ids]
    if to_insert:
        client.table("bkt_parameters").upsert(to_insert).execute()
        print(f"Inserted {len(to_insert)} rows into bkt_parameters")
    else:
        print("bkt_parameters already populated")


def ensure_question_metadata(client):
    existing = client.table("question_metadata_cache").select("question_id").execute().data or []
    existing_ids = {row.get("question_id") for row in existing}
    to_insert = [row for row in SEED_QUESTIONS if row["question_id"] not in existing_ids]
    if to_insert:
        client.table("question_metadata_cache").upsert(to_insert).execute()
        print(f"Inserted {len(to_insert)} rows into question_metadata_cache")
    else:
        print("question_metadata_cache already populated")


def main():
    load_env()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        raise SystemExit(1)

    client = create_client(url, key)

    ensure_bkt_parameters(client)
    ensure_question_metadata(client)

    print("Seeding complete.")


if __name__ == "__main__":
    main()
