from fastapi.testclient import TestClient

from app.main import app
from tests.test_resume_generation import sample_payload

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-secret-key"}


def test_responses_include_request_id_and_security_headers():
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.headers["X-Request-ID"] == "test-request-id"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_document_extract_supports_text_upload():
    response = client.post(
        "/api/v1/documents/extract",
        headers=AUTH_HEADERS,
        files={"file": ("resume.txt", b"Python FastAPI CrewAI resume", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Python FastAPI CrewAI resume"
    assert response.json()["character_count"] == 28


def test_document_extract_rejects_unsupported_file_type():
    response = client.post(
        "/api/v1/documents/extract",
        headers=AUTH_HEADERS,
        files={"file": ("resume.bin", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_resume_export_text_returns_downloadable_plain_text():
    generated = client.post(
        "/api/v1/resume/generate",
        json=sample_payload(),
        headers=AUTH_HEADERS,
    )
    assert generated.status_code == 200

    response = client.post(
        "/api/v1/resume/export/text",
        json=generated.json(),
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "Professional Summary" in response.text
    assert "ATS Analysis" in response.text
