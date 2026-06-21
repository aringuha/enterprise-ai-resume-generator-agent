from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def sample_payload():
    return {
        "candidate_profile": {
            "name": "Test User",
            "summary": "AI engineer with Python, FastAPI, CrewAI, Ollama, Kafka, Azure, and Kubernetes experience.",
            "skills": ["Python", "FastAPI", "CrewAI", "Ollama", "Kafka", "Azure", "Kubernetes", "SQL", "GenAI"],
            "experience": [{
                "company": "Example Corp",
                "title": "AI Engineer",
                "years": 5,
                "responsibilities": ["built AI resume generator", "designed CrewAI workflow", "implemented logging and monitoring"]
            }],
            "projects": [{
                "name": "Enterprise AI Resume Generator",
                "description": "Built a multi-agent resume workflow",
                "technologies": ["FastAPI", "CrewAI", "Ollama"],
                "outcomes": ["Improved ATS targeting"]
            }],
            "education": ["MS Computer Science"],
            "certifications": ["AWS Solutions Architect"]
        },
        "target_job": {
            "title": "Principal AI Architect",
            "company": "Example Bank",
            "description": "Requires GenAI, agentic AI, FastAPI, CrewAI, Ollama, Python, API architecture, governance, observability, and security."
        }
    }

def test_generate_resume_requires_api_key():
    response = client.post("/api/v1/resume/generate", json=sample_payload())
    assert response.status_code in [401, 422]

def test_generate_resume_success():
    response = client.post("/api/v1/resume/generate", json=sample_payload(), headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["agentic_framework"] == "CrewAI sequential multi-agent crew"
    assert body["orchestration_mode"] == "CrewAI Process.sequential"
    assert len(body["resume_content"]["project_descriptions"]) > 0


def test_generate_resume_accepts_bearer_token():
    response = client.post(
        "/api/v1/resume/generate",
        json=sample_payload(),
        headers={"Authorization": "Bearer dev-secret-key"},
    )

    assert response.status_code == 200


def test_auth_validate_accepts_bearer_token():
    response = client.get("/api/v1/auth/validate", headers={"Authorization": "Bearer dev-secret-key"})

    assert response.status_code == 200
    assert response.json() == {"status": "authenticated"}
