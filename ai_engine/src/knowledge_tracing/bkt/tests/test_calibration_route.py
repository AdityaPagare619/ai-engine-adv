# ai_engine/tests/integration/test_calibration_route.py
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
async def test_calibration_returns_reliability_bins(supabase):
    # Seed minimal logs to produce bins
    supabase.table("bkt_update_logs").upsert([
        {
            "student_id": "s_cal",
            "concept_id": "calib_concept",
            "previous_mastery": 0.40,
            "new_mastery": 0.55,
            "is_correct": True,
            "response_time_ms": 2000,
            "question_id": "Q_CAL_1",
            "timestamp": "2025-09-18T10:00:00Z",
            "params_used": {"learn_rate": 0.25, "slip_rate": 0.10, "guess_rate": 0.20}
        },
        {
            "student_id": "s_cal",
            "concept_id": "calib_concept",
            "previous_mastery": 0.55,
            "new_mastery": 0.52,
            "is_correct": False,
            "response_time_ms": 2800,
            "question_id": "Q_CAL_2",
            "timestamp": "2025-09-18T10:05:00Z",
            "params_used": {"learn_rate": 0.25, "slip_rate": 0.10, "guess_rate": 0.20}
        },
    ]).execute()

    async with httpx.AsyncClient(base_url=API_BASE) as client:
        resp = await client.get("/ai/trace/calibration", params={
            "concept_id": "calib_concept",
            "bins": 10
        })
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert "points" in payload and isinstance(payload["points"], list)
    assert payload["n_bins"] == 10
    # Points include counts; at least one bin should have nonzero count
    assert any(p.get("count", 0) > 0 for p in payload["points"])
