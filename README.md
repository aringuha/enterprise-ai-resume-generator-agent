# Enterprise AI Resume Generator Agent

A multi-agent AI resume generator built with **CrewAI**, **Ollama**, **FastAPI**, and **Streamlit**. The entire application runs as three Docker containers with a single command.

## Architecture

```text
Streamlit UI (port 8501)
        ↓
FastAPI API (port 8000)
        ↓
Ollama LLM (port 11434)
```

Four CrewAI agents run sequentially inside the FastAPI service:

1. **Profile Analyzer** — extracts skills, experience, level, and domain
2. **ATS Optimizer** — identifies missing keywords and estimates ATS score
3. **Resume Writer** — generates professional resume content
4. **Reviewer** — validates grammar, consistency, and professionalism

## Technology Stack

| Layer | Technology |
|---|---|
| Agentic Framework | CrewAI (sequential multi-agent crew) |
| LLM Runtime | Ollama (llama3.2 by default) |
| API | FastAPI with Pydantic models |
| Frontend | Streamlit |
| Auth | JWT bearer token, static dev token, X-API-Key |
| Observability | Structured JSON logs, request IDs, `/health`, `/ready`, `/metrics` |
| Deployment | Docker Compose / Kubernetes scaffold |
| Testing | Pytest |

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1. Clone and configure

```bash
git clone https://github.com/aringuha/enterprise-ai-resume-generator-agent.git
cd enterprise-ai-resume-generator-agent
cp .env.example .env
```

### 2. Start the application

```bash
docker compose up --build
```

This pulls the Ollama image, downloads the llama3.2 model, builds the app image, and starts all three containers. The first run takes a few minutes for the model download.

### 3. Use the application

| Service | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

Login token for local development: `dev-secret-key`

### 4. Stop the application

```bash
docker compose down
```

To also delete downloaded models:

```bash
docker compose down -v
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness check |
| `/ready` | GET | Readiness check (includes Ollama) |
| `/metrics` | GET | Prometheus-style metrics |
| `/metrics/json` | GET | JSON metrics snapshot |
| `/api/v1/auth/validate` | GET | Validate login credentials |
| `/api/v1/documents/extract` | POST | Extract text from PDF/DOCX/TXT/Markdown |
| `/api/v1/resume/generate` | POST | Run the multi-agent resume workflow |
| `/api/v1/resume/export/text` | POST | Export resume as downloadable text |

### Example API call

```bash
curl -X POST "http://localhost:8000/api/v1/resume/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "candidate_profile": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "555-555-5555",
      "location": "Cary, NC",
      "summary": "Enterprise architect with AI and cloud experience.",
      "skills": ["Python", "FastAPI", "CrewAI", "GenAI", "Kubernetes", "SQL"],
      "experience": [
        {
          "company": "Example Corp",
          "title": "Principal Engineer",
          "years": 5,
          "responsibilities": ["Designed AI workflows", "Built API services"]
        }
      ],
      "education": ["MS Computer Science"],
      "certifications": ["AWS Solutions Architect"]
    },
    "target_job": {
      "title": "Principal AI Architect",
      "company": "Acme Inc",
      "description": "Requires GenAI, Agentic AI, architecture, APIs, cloud, and observability."
    }
  }'
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest -q
```

---

## Project Structure

```text
├── app/
│   ├── api/routes.py              # API endpoints
│   ├── core/
│   │   ├── config.py              # Settings from .env
│   │   ├── logging_config.py      # Structured JSON logging
│   │   ├── middleware.py          # Request IDs, rate limiting, security headers
│   │   └── security.py           # JWT / bearer / API key auth
│   ├── crew/resume_crew.py       # CrewAI agent definitions and crew
│   ├── models/resume_models.py   # Pydantic request/response models
│   ├── services/
│   │   ├── document_parser.py    # PDF/DOCX/TXT extraction
│   │   ├── metrics.py            # Prometheus-style metrics
│   │   ├── ollama_client.py      # Ollama health and readiness
│   │   └── orchestrator.py       # Resume generation workflow
│   └── main.py                   # FastAPI app entry point
├── frontend/streamlit_app.py     # Streamlit UI
├── deploy/kubernetes/            # Kubernetes deployment scaffold
├── tests/                        # Pytest test suite
├── .github/workflows/tests.yml   # CI workflow
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Environment Variables

Copy `.env.example` to `.env` before running. Key variables:

| Variable | Purpose |
|---|---|
| `API_KEY` | API key for `X-API-Key` header |
| `BEARER_TOKEN` | Static dev bearer token |
| `JWT_SECRET` | Secret for signed JWT tokens |
| `OLLAMA_MODEL` | Ollama model name (default: `llama3.2`) |

For slower machines, switch to a smaller model:

```text
OLLAMA_MODEL=phi3
```

---

## Security

Three authentication methods are supported:

- `Authorization: Bearer <signed-jwt>` — production-style
- `Authorization: Bearer <dev-token>` — local development
- `X-API-Key: <api-key>` — backward compatibility

The Streamlit UI includes a login gate. For production, replace the static token with an OIDC provider (Google Workspace, Microsoft Entra ID, Okta).

---

## Advanced: Local Development Without Docker

If you prefer running without containers:

```bash
# Terminal 1: Start Ollama
ollama serve
ollama pull llama3.2

# Terminal 2: Start FastAPI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Terminal 3: Start Streamlit
source .venv/bin/activate
streamlit run frontend/streamlit_app.py
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Containers won't start | Make sure Docker Desktop is running |
| Ollama model download hangs | Check internet connection; restart with `docker compose down && docker compose up --build` |
| `Unauthorized` API response | Include `X-API-Key: dev-secret-key` header |
| CrewAI is slow | Use a smaller model: set `OLLAMA_MODEL=phi3` in `.env` |
| Port conflict on 11434 | The container maps to host port `11435` to avoid conflicts with a local Ollama install |
