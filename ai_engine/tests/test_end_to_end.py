# tests/test_end_to_end.py
import pytest
from fastapi.testclient import TestClient
from ai_engine.main import app  # Assuming your FastAPI app entrypoint

client = TestClient(app)

def test_allocate_time_endpoint():
    payload = {
        "student_id": "student123",
        "question_id": "q456",
        "base_time_ms": 30000,
        "stress_level": 0.5,
        "fatigue_level": 0.3,
        "mastery": 0.7,
        "difficulty": 1.2,
        "session_elapsed_ms": 600000
    }
    response = client.post("/ai/trace/pacing/allocate-time", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "final_time_ms" in data
    assert data["final_time_ms"] >= 15000

def test_fairness_update_and_report():
    update_payload = {
        "group": "female",
        "mastery_scores": [0.6, 0.7, 0.65]
    }
    response = client.post("/ai/trace/fairness/update", json=update_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "updated"

    response = client.get("/ai/trace/fairness/report")
    assert response.status_code == 200
    data = response.json()
    assert "averages" in data
    assert "disparity" in data

def test_calibration_fit_and_calibrate():
    fit_payload = {
        "logits": [[1.2, 0.8], [0.5, 1.5], [1.0, 1.0]],
        "labels": [0, 1, 0]
    }
    response = client.post("/ai/trace/calibration/fit", json=fit_payload)
    assert response.status_code == 200
    temperature = response.json().get("temperature")
    assert temperature is not None

    calibrate_payload = {
        "logits": [[1.2, 0.8], [0.5, 1.5], [1.0, 1.0]]
    }
    response = client.post("/ai/trace/calibration/calibrate", json=calibrate_payload)
    assert response.status_code == 200
    probs = response.json().get("probabilities")
    assert probs is not None
