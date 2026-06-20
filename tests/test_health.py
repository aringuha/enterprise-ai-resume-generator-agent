from fastapi.testclient import TestClient
from app.main import app
from app.services import ollama_client

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["agentic_framework"] == "CrewAI"


def test_ready_returns_ready_when_ollama_is_available(monkeypatch):
    monkeypatch.setattr(ollama_client.ollama_client, "is_available", lambda: True)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_returns_503_when_ollama_is_required_but_unavailable(monkeypatch):
    monkeypatch.setattr(ollama_client.ollama_client, "is_available", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_metrics_endpoint_returns_prometheus_text():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "resume_generator_requests_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_json_endpoint_returns_snapshot():
    response = client.get("/metrics/json")

    assert response.status_code == 200
    assert "total_requests" in response.json()
