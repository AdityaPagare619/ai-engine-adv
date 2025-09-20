# ai_engine/tests/integration/test_bkt_with_context.py
import asyncio
import os
import pytest
import httpx
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:54321")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
API_BASE = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@pytest.mark.asyncio
async def test_update_with_context_adjusts_params_and_updates_state(supabase):
    # Arrange: parameter row and question metadata cache
    supabase.table("bkt_parameters").upsert({
        "concept_id": "kinematics_basic",
        "learn_rate": 0.25,
        "slip_rate": 0.10,
        "guess_rate": 0.20
    }).execute()

    supabase.table("question_metadata_cache").upsert({
        "question_id": "PHY_MECH_0001",
        "subject": "Physics",
        "topic": "Kinematics",
        "difficulty_calibrated": 1.2,
        "bloom_level": "Apply",
        "estimated_time_seconds": 120,
        "required_process_skills": ["kinematics", "problem_solving"],
        "question_type": "Numeric"
    }).execute()

    # Reset any previous state if you maintain a reset RPC; otherwise rely on initial default
    # supabase.rpc("reset_bkt_state", {"student_id":"s1","concept_id":"kinematics_basic"}).execute()

    # Act: call update endpoint with context
    async with httpx.AsyncClient(base_url=API_BASE) as client:
        resp = await client.post("/ai/trace/update", json={
            "student_id": "s1",
            "concept_id": "kinematics_basic",
            "question_id": "PHY_MECH_0001",
            "is_correct": True,
            "response_time_ms": 2500
        })

    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Assert: adjustments present and feasible
    adj = body["adjusted_params"]
    assert 0.001 <= adj["slip_rate"] <= 0.3
    assert 0.001 <= adj["guess_rate"] <= 0.5
    assert 0.001 <= adj["learn_rate"] <= 0.5
    # Identifiability and ordering (loose check)
    assert (adj["slip_rate"] + adj["guess_rate"]) < 0.999
    assert (1.0 - adj["slip_rate"]) > adj["guess_rate"]

    # Assert: mastery increased from default ~0.5 after correct
    assert body["new_mastery"] > body["previous_mastery"]
    assert 0.0 <= body["p_correct_pred"] <= 1.0

    # Verify persisted state reflects new mastery
    state = supabase.table("bkt_knowledge_states") \
        .select("mastery_probability, practice_count") \
        .eq("student_id", "s1") \
        .eq("concept_id", "kinematics_basic") \
        .single().execute().data
    assert state is not None
    assert pytest.approx(state["mastery_probability"], rel=1e-6) == body["new_mastery"]
    assert int(state["practice_count"]) >= 1
