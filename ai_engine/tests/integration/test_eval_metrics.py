# ai_engine/tests/integration/test_evaluate_metrics.py
import os
import pytest
import httpx

API_BASE = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_evaluate_window_returns_metrics_and_recommendation():
    async with httpx.AsyncClient(base_url=API_BASE) as client:
        resp = await client.post("/ai/trace/evaluate", json={
            "concept_id": "kinematics_basic",
            "start_ts": None,
            "end_ts": None
        })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Basic presence checks
    for key in ["next_step_auc", "next_step_accuracy", "brier_score", "calibration_error", "trajectory_validity", "recommendation"]:
        assert key in body
    # Range checks
    assert 0.0 <= body["next_step_auc"] <= 1.0
    assert 0.0 <= body["next_step_accuracy"] <= 1.0
    assert 0.0 <= body["brier_score"] <= 1.0
    assert 0.0 <= body["calibration_error"] <= 1.0
    assert 0.0 <= body["trajectory_validity"] <= 1.0
    assert body["recommendation"] in ("PASS", "NEEDS_IMPROVEMENT")
