import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_asset_invalid_type():
    response = client.post(
        "/assets/upload",
        data={"question_id": "QID123"},
        files={"file": ("test.txt", b"file content", "text/plain")}
    )
    assert response.status_code == 400

@pytest.mark.parametrize("file_name,content_type", [
    ("image.png", "image/png"),
    ("image.jpg", "image/jpeg"),
    ("image.webp", "image/webp"),
])
def test_upload_asset_success(file_name, content_type):
    response = client.post(
        "/assets/upload",
        data={"question_id": "QID123"},
        files={"file": (file_name, b"fakeimagecontent", content_type)}
    )
    assert response.status_code == 200
    assert "asset_id" in response.json()
