# Capstone Project Submission Summary

## Project Title
Enterprise AI Resume Generator Agent

## Final Stack

- Agentic Framework: CrewAI
- LLM Runtime: Ollama
- Frontend: Streamlit
- API: FastAPI
- Schemas: Pydantic
- Security: API key authentication
- Observability: Python logging and `/metrics`
- Deployment: Docker and Docker Compose

## Mandatory Architecture Mapping

| Assignment Requirement | Implementation |
|---|---|
| User/API Request | Streamlit UI and POST `/api/v1/resume/generate` |
| FastAPI Endpoint | `app/api/routes.py` |
| Authentication Layer | `app/core/security.py` |
| Orchestrator | `app/services/orchestrator.py` |
| Agentic Framework | `app/crew/resume_crew.py` using CrewAI |
| Profile Analyzer Agent | CrewAI Agent in `app/crew/resume_crew.py` |
| ATS Optimization Agent | CrewAI Agent in `app/crew/resume_crew.py` |
| Resume Writer Agent | CrewAI Agent in `app/crew/resume_crew.py` |
| Reviewer Agent | CrewAI Agent in `app/crew/resume_crew.py` |
| Structured JSON Response | `app/models/resume_models.py` |
| Logs + Monitoring | `app/core/logging_config.py`, `/metrics` |
| Frontend | `frontend/streamlit_app.py` |
| Local LLM | `app/services/ollama_client.py` |

## CrewAI Flow

```text
Profile Analyzer Agent
  ↓
ATS Optimization Agent
  ↓
Resume Writer Agent
  ↓
Reviewer Agent
```
