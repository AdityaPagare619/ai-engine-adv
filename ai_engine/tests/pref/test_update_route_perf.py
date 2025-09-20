# ai_engine/tests/perf/test_update_route_perf.py
import os
import time
import asyncio
import httpx
import numpy as np
import pytest

API_BASE = os.getenv("AI_ENGINE_BASE_URL", "http://localhost:8000")

async def _call_update(client, i):
    payload = {
        "student_id": f"s_perf_{i%5}",
        "concept_id": "kinematics_basic",
        "question_id": None,
        "is_correct": bool(i % 2),
        "response_time_ms": 2000 + (i % 7) * 100
    }
    t0 = time.perf_counter()
    resp = await client.post("/ai/trace/update", json=payload)
    t1 = time.perf_counter()
    assert resp.status_code == 200, resp.text
    return (t1 - t0) * 1000.0  # ms

async def _call_select(client, i):
    params = {
        "student_id": f"s_perf_{i%5}",
        "concept_id": "kinematics_basic",
        "subject": "Physics",
        "topic": "Kinematics"
    }
    t0 = time.perf_counter()
    resp = await client.get("/ai/trace/select", params=params)
    t1 = time.perf_counter()
    assert resp.status_code == 200, resp.text
    return (t1 - t0) * 1000.0  # ms

@pytest.mark.asyncio
async def test_p95_latency_under_budget():
    n = 40
    async with httpx.AsyncClient(base_url=API_BASE, timeout=10.0) as client:
        # Warm-up
        await _call_update(client, 0)
        await _call_select(client, 0)

        upd_times = await asyncio.gather(*[_call_update(client, i) for i in range(n)])
        sel_times = await asyncio.gather(*[_call_select(client, i) for i in range(n)])

    def p95(xs):
        return float(np.percentile(np.array(xs), 95))

    p95_update = p95(upd_times)
    p95_select = p95(sel_times)
    # Targets aligned with blueprint guidance (tighten in prod)
    assert p95_update < 100.0, f"Update p95 too high: {p95_update} ms"
    assert p95_select < 120.0, f"Select p95 too high: {p95_select} ms"
