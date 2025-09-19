import asyncio
import httpx
import pytest
from supabase import create_client

SUPABASE_URL = "https://your-supabase-url"
SUPABASE_KEY = "service-role-key"

@pytest.fixture(scope="module")
def supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@pytest.mark.asyncio
async def test_bkt_full_cycle(supabase):
    # Arrange: ensure parameter and initial state exist
    supabase.table("bkt_parameters").upsert({
        "concept_id": "test_concept",
        "learn_rate": 0.3,
        "slip_rate": 0.1,
        "guess_rate": 0.2
    }).execute()
    await supabase.rpc("reset_bkt_state", {"student_id": "00000000-0000-0000-0000-000000000001", "concept_id":"test_concept"})

    # Act: call the API endpoint
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        resp = await client.post("/ai/trace/update", json={
            "student_id": "00000000-0000-0000-0000-000000000001",
            "concept_id": "test_concept",
            "is_correct": True,
            "response_time_ms": 1500
        })
        assert resp.status_code == 200
        body = resp.json()

    # Assert: verify state updated in DB
    state = supabase.table("bkt_knowledge_states")\
        .select("mastery_probability, practice_count")\
        .eq("student_id", "00000000-0000-0000-0000-000000000001")\
        .eq("concept_id", "test_concept")\
        .single().execute().data

    assert body["new_mastery"] == float(state["mastery_probability"])
    assert state["practice_count"] == 1
    assert body["learning_occurred"] is True
