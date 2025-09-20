# ai_engine/tests/integration/test_selection_route.py
import os
import pytest
import httpx
from supabase import create_client

API_BASE = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:54321")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

@pytest.fixture(scope="module")
def supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@pytest.mark.asyncio
async def test_selection_route_returns_chosen_and_scores(supabase):
    # Seed candidate metadata
    supabase.table("question_metadata_cache").upsert([
        {"question_id": "PH1", "subject": "Physics", "topic": "Kinematics", "difficulty_calibrated": 0.8, "estimated_time_seconds": 90},
        {"question_id": "PH2", "subject": "Physics", "topic": "Kinematics", "difficulty_calibrated": 1.5, "estimated_time_seconds": 120},
        {"question_id": "PH3", "subject": "Physics", "topic": "Kinematics", "difficulty_calibrated": 0.2, "estimated_time_seconds": 60},
    ]).execute()

    # Seed state
    supabase.table("bkt_knowledge_states").upsert({
        "student_id": "s_bandit",
        "concept_id": "kinematics_basic",
        "mastery_probability": 0.55,
        "practice_count": 8
    }).execute()

    async with httpx.AsyncClient(base_url=API_BASE) as client:
        resp = await client.get("/ai/trace/select", params={
            "student_id": "s_bandit",
            "concept_id": "kinematics_basic",
            "subject": "Physics",
            "topic": "Kinematics",
        })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chosen_question_id"] in {"PH1", "PH2", "PH3"}
    assert "scores" in body["debug"] and len(body["debug"]["scores"]) >= 1
