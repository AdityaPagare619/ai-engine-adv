# tests/test_end_to_end.py
import pytest
from fastapi.testclient import TestClient
from ai_engine.main import app

client = TestClient(app)

def test_pacing_exam_caps():
    payload = {
        "student_id": "s1",
        "question_id": "q1",
        "base_time_ms": 600000,
        "stress_level": 0.4,
        "fatigue_level": 0.2,
        "mastery": 0.6,
        "difficulty": 1.0,
        "session_elapsed_ms": 45*60*1000,
        "exam_code": "NEET"
    }
    r = client.post("/ai/trace/pacing/allocate-time", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["final_time_ms"] <= 90_000  # NEET per-question cap
    assert "breakdown" in data

def test_calibration_per_exam_subject():
    fit = {
        "logits": [[1.2, 0.8], [0.5, 1.5], [1.0, 1.0]],
        "labels": [0, 1, 0],
        "exam_code": "JEE_Advanced",
        "subject": "physics"
    }
    r = client.post("/ai/trace/calibration/fit", json=fit)
    assert r.status_code == 200
    T = r.json()["temperature"]
    assert T > 0

    apply_req = {
        "logits": [[1.2, 0.8], [0.5, 1.5], [1.0, 1.0]],
        "exam_code": "JEE_Advanced",
        "subject": "physics"
    }
    r = client.post("/ai/trace/calibration/apply", json=apply_req)
    assert r.status_code == 200
    probs = r.json()["probabilities"]
    assert len(probs) == 3

def test_fairness_segmented():
    up = {
        "exam_code": "NEET",
        "subject": "biology",
        "group": "female",
        "mastery_scores": [0.6, 0.65, 0.7]
    }
    r = client.post("/ai/trace/fairness/update", json=up)
    assert r.status_code == 200

    up2 = {
        "exam_code": "NEET",
        "subject": "biology",
        "group": "male",
        "mastery_scores": [0.55, 0.6, 0.58]
    }
    r = client.post("/ai/trace/fairness/update", json=up2)
    assert r.status_code == 200

    rep = {"exam_code": "NEET", "subject": "biology"}
    r = client.post("/ai/trace/fairness/report", json=rep)
    assert r.status_code == 200
    data = r.json()
    assert "averages" in data and "disparity" in data
