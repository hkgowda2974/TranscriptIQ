import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["experts_loaded"] == 3


def test_transcripts_endpoint(client):
    response = client.get("/api/transcripts")
    assert response.status_code == 200
    data = response.json()
    assert len(data["experts"]) == 3
    assert len(data["questions"]) == 6


def test_matrix_endpoint(client):
    response = client.get("/api/matrix")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 18  # 6 questions * 3 experts


def test_synthesis_endpoint(client):
    response = client.get("/api/synthesis")
    assert response.status_code == 200
    data = response.json()
    assert len(data["common_themes"]) >= 1
    assert len(data["disagreements"]) >= 1


def test_custom_qa_endpoint(client):
    response = client.post("/api/qa", json={"query": "What are the main barriers in the UK?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer_summary" in data
    assert len(data["evidence"]) >= 1
