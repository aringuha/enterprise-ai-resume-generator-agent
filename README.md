# Enterprise AI Resume Generator Agent

## 1. Project Overview

The **Enterprise AI Resume Generator Agent** is a production-style capstone project that demonstrates an enterprise-grade AI workflow, not just a chatbot.

The system accepts a candidate profile and a target job description, then uses a multi-agent AI workflow to:

1. Analyze the candidate profile
2. Identify ATS keywords and resume gaps
3. Generate professional resume content
4. Review the output for quality and professionalism
5. Return a structured JSON response
6. Display results through a Streamlit frontend

This project is designed to demonstrate:

- Multi-agent AI architecture
- CrewAI-based agent orchestration
- Local LLM execution with Ollama
- FastAPI backend API
- Streamlit frontend
- API authentication
- Structured Pydantic models
- Logging and observability
- Docker readiness
- Automated testing
- GitHub/GitLab submission readiness

---

## 2. Final Technology Stack

| Layer | Technology |
|---|---|
| Agentic Framework | CrewAI |
| LLM Runtime | Ollama |
| LLM Model | llama3.2 by default |
| API Framework | FastAPI |
| Frontend | Streamlit |
| Data Validation | Pydantic |
| Authentication | JWT bearer token, static dev bearer token, and `X-API-Key` |
| Observability | Structured logs, request IDs, `/metrics`, `/metrics/json`, `/health`, `/ready` |
| File Processing | PDF/DOCX/TXT/Markdown extraction |
| Testing | Pytest |
| Deployment | Docker / Docker Compose / Kubernetes scaffold |
| Version Control | GitHub or GitLab |

---

## 3. Architectural Design

```text
User / Browser
  ↓
Streamlit UI
  ├── Secure login gate
  ├── Resume upload or manual profile fields
  ├── Job description upload or paste
  └── TXT / JSON download
  ↓
FastAPI API Layer
  ├── CORS allowlist
  ├── Request ID middleware
  ├── Security headers
  ├── Rate limiting
  ├── Audit-style logs
  └── Auth dependency
       ├── JWT bearer token
       ├── Static development bearer token
       └── X-API-Key compatibility
  ↓
Application Services
  ├── Document extraction service
  ├── Resume orchestrator
  ├── Metrics service
  └── Ollama client / readiness checks
  ↓
CrewAI Sequential Multi-Agent Workflow
  ├── Profile Analyzer Agent
  ├── ATS Optimization Agent
  ├── Resume Writer Agent
  └── Reviewer Agent
  ↓
Ollama Local LLM Runtime
  ↓
Structured Pydantic JSON Response
  ↓
Operational Endpoints
  ├── /health
  ├── /ready
  ├── /metrics
  └── /metrics/json
```

### 3.1 Backend Layers

| Layer | Responsibility |
|---|---|
| API routes | Accept resume generation, document extraction, auth validation, export requests |
| Security | Validate JWT bearer tokens, static bearer tokens, and API keys |
| Middleware | Add request IDs, rate limiting, CORS, security headers, and audit logs |
| Orchestrator | Coordinates the resume generation workflow |
| Agent workflow | Runs the CrewAI sequential agents |
| Models | Enforce structured request/response contracts with Pydantic |
| Services | Ollama access, metrics, document parsing, export formatting |

### 3.2 Key API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /ready` | Readiness check, including Ollama availability |
| `GET /metrics` | Prometheus-style metrics |
| `GET /metrics/json` | JSON metrics snapshot |
| `GET /api/v1/auth/validate` | Validate frontend login credentials |
| `POST /api/v1/documents/extract` | Extract text from PDF/DOCX/TXT/Markdown upload |
| `POST /api/v1/resume/generate` | Run the multi-agent resume workflow |
| `POST /api/v1/resume/export/text` | Export generated resume response as downloadable text |

### 3.3 Security Design

The application supports three authentication styles:

- `Authorization: Bearer <signed-jwt>` for production-style API access
- `Authorization: Bearer <dev-token>` for local development
- `X-API-Key: <api-key>` for backward compatibility

The Streamlit UI has a login gate and then sends both bearer and API-key headers to the FastAPI backend. In a true enterprise deployment, replace the static development token with Google Workspace, Microsoft Entra ID, Okta, or another OIDC provider.

### 3.4 Observability Design

The API includes:

- Structured JSON logging
- Request ID propagation through `X-Request-ID`
- Audit-style request completion logs
- Prometheus-compatible metrics at `/metrics`
- JSON metrics at `/metrics/json`
- Liveness and readiness endpoints for Docker/Kubernetes health checks

### 3.5 Deployment Design

The project can run in three modes:

- Local Python virtual environment
- Docker Compose on a developer machine
- Kubernetes using the scaffold in `deploy/kubernetes/enterprise-ai-resume-generator.yaml`

---

## 4. Agentic Framework Explanation

### What agentic framework is used?

This project uses **CrewAI** as the agentic framework.

CrewAI is responsible for defining and coordinating multiple role-based agents.

### Is Ollama the agentic framework?

No.

**Ollama is the local LLM runtime.**

CrewAI is the agentic framework. Ollama runs the local language model that the agents call.

### How to explain this in a demo

Use this explanation:

> This project uses CrewAI as the agentic framework. The workflow is implemented as a sequential multi-agent crew with four agents: Profile Analyzer, ATS Optimizer, Resume Writer, and Reviewer. Ollama provides local LLM inference, FastAPI exposes the workflow through a secure API, Streamlit provides the frontend, and Pydantic enforces structured input and output.

---

## 5. Required Agents

### 5.1 Profile Analyzer Agent

Responsible for analyzing:

- Candidate skills
- Experience
- Projects
- Education
- Certifications
- Candidate level
- Primary domain

Example output:

```json
{
  "candidate_level": "Mid-Level",
  "primary_domain": "Data Analytics",
  "years_experience": 5
}
```

### 5.2 ATS Optimization Agent

Responsible for:

- Identifying ATS keywords
- Comparing job description with candidate profile
- Finding missing keywords
- Estimating ATS score
- Suggesting formatting improvements

Example output:

```json
{
  "missing_keywords": ["Power BI", "SQL"],
  "ats_score": 78
}
```

### 5.3 Resume Writer Agent

Responsible for generating:

- Professional summary
- Skills section
- Experience bullets
- Project descriptions

### 5.4 Reviewer Agent

Responsible for validating:

- Grammar
- Consistency
- Formatting
- Enterprise professionalism
- Final recommendations

---

## 6. Project Folder Structure

```text
enterprise_ai_resume_generator_crewai/
├── .github/
│   └── workflows/
│       └── tests.yml
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging_config.py
│   │   ├── middleware.py
│   │   └── security.py
│   ├── crew/
│   │   └── resume_crew.py
│   ├── models/
│   │   └── resume_models.py
│   ├── services/
│   │   ├── document_parser.py
│   │   ├── metrics.py
│   │   ├── ollama_client.py
│   │   └── orchestrator.py
│   └── main.py
├── deploy/
│   └── kubernetes/
│       └── enterprise-ai-resume-generator.yaml
├── frontend/
│   └── streamlit_app.py
├── tests/
│   ├── test_enterprise_features.py
│   ├── test_health.py
│   ├── test_metrics.py
│   ├── test_ollama_client.py
│   ├── test_resume_generation.py
│   ├── test_resume_workflow.py
│   └── test_security.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── README.md
├── PROJECT_SUMMARY.md
└── ARCHITECTURE.md
```

---

## 7. Prerequisites

Install these before running the project:

### Required

- Python 3.10, 3.11, or 3.12 recommended
- Git
- A terminal or command prompt

### Recommended

- VS Code
- GitHub Desktop or Git command line
- Docker Desktop
- Ollama, only if running without the Ollama container

---

## 8. Install Ollama

This section is only required when running the app without the Ollama Docker container.

Download and install Ollama for your operating system.

After installation, start Ollama:

```bash
ollama serve
```

In another terminal, pull the default model:

```bash
ollama pull llama3.2
```

If your laptop is slower, use a smaller model:

```bash
ollama pull phi3
```

Then update `.env`:

```text
OLLAMA_MODEL=phi3
```

Check installed models:

```bash
ollama list
```

---

## 9. Local Setup

### 9.1 Clone or unzip the project

If using ZIP:

```bash
unzip enterprise_ai_resume_generator_crewai_TESTED_README.zip
cd enterprise_ai_resume_generator_crewai
```

If using GitHub/GitLab:

```bash
git clone <your-repository-url>
cd enterprise_ai_resume_generator_crewai
```

### 9.2 Create virtual environment

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 9.3 Install dependencies

```bash
pip install -r requirements.txt
```

### 9.4 Create environment file

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

---

## 10. Environment Variables

The `.env` file controls runtime configuration.

```text
APP_NAME=Enterprise AI Resume Generator Agent
ENVIRONMENT=local
API_KEY=dev-secret-key
BEARER_TOKEN=dev-secret-key
JWT_SECRET=dev-jwt-secret-change-me-32-bytes-min
JWT_ALGORITHM=HS256
JWT_ISSUER=enterprise-ai-resume-generator
LOG_LEVEL=INFO

USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT_SECONDS=90

FASTAPI_BASE_URL=http://127.0.0.1:8000
```

### Important variables

| Variable | Purpose |
|---|---|
| `API_KEY` | API key required by FastAPI endpoint |
| `BEARER_TOKEN` | Static development bearer token accepted in the `Authorization` header |
| `JWT_SECRET` | Secret used to verify signed JWT bearer tokens |
| `JWT_ALGORITHM` | JWT signing algorithm |
| `JWT_ISSUER` | Expected JWT issuer |
| `USE_OLLAMA` | Enables local LLM usage |
| `OLLAMA_BASE_URL` | Local Ollama server URL |
| `OLLAMA_MODEL` | Ollama model name |
| `FASTAPI_BASE_URL` | URL used by Streamlit to call backend |

---

## 10.1 Enterprise Readiness Features

The project includes production-style features beyond the core resume workflow:

- API authentication with signed JWT bearer tokens, static development bearer tokens, and legacy `X-API-Key` support
- `/health` liveness endpoint
- `/ready` readiness endpoint that checks Ollama availability
- `/metrics` Prometheus-style text metrics
- `/metrics/json` JSON metrics snapshot
- Docker Compose healthchecks for the API and Streamlit services
- GitHub Actions test workflow in `.github/workflows/tests.yml`
- Project input support in the candidate profile model and Streamlit UI

---

## 11. Run the FastAPI Backend

Make sure your virtual environment is active.

```bash
uvicorn app.main:app --reload
```

FastAPI will run at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Metrics:

```text
http://127.0.0.1:8000/metrics
```

---

## 12. Run the Streamlit Frontend

Open a second terminal, activate the same virtual environment, and run:

```bash
streamlit run frontend/streamlit_app.py
```

Streamlit will open at:

```text
http://localhost:8501
```

Use the form to enter:

- Candidate profile
- Skills
- Experience
- Education
- Certifications
- Target company
- Target role
- Job description

Then click:

```text
Generate Resume
```

---

## 13. Test the API with curl

Make sure FastAPI is running.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resume/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{
    "candidate_profile": {
      "name": "Arindra Guha",
      "email": "arin@example.com",
      "phone": "555-555-5555",
      "location": "Cary, NC",
      "summary": "Enterprise architect with AI, cloud, distributed systems, API, security, and observability experience.",
      "skills": ["Python", "FastAPI", "Streamlit", "Ollama", "CrewAI", "GenAI", "Agentic AI", "Kafka", "Azure", "Kubernetes", "SQL"],
      "experience": [
        {
          "company": "Example Corp",
          "title": "Principal Engineer",
          "years": 5,
          "responsibilities": [
            "Built local AI resume generator using Ollama",
            "Designed FastAPI endpoints and CrewAI workflow",
            "Implemented logging, metrics, API authentication, and Streamlit UI"
          ]
        }
      ],
      "education": ["PhD Electrical Engineering", "MBA"],
      "certifications": ["PMP", "AWS Solutions Architect"]
    },
    "target_job": {
      "title": "Principal AI Architect",
      "company": "Wells Fargo",
      "description": "Requires GenAI, Agentic AI, architecture, governance, APIs, cloud, security, observability, and responsible AI."
    }
  }'
```

Expected response includes:

```json
{
  "agentic_framework": "CrewAI sequential multi-agent crew",
  "orchestration_mode": "CrewAI Process.sequential",
  "llm_provider": "Ollama local LLM"
}
```

---

## 14. Run Automated Tests

```bash
source .venv/bin/activate
pytest -q
```

Expected result:

```text
29 passed
```

The tests validate:

- FastAPI health endpoint
- API key requirement
- JWT/bearer token auth
- Request ID and security headers
- Readiness and metrics endpoints
- Document upload extraction
- Resume export endpoint
- Resume generation endpoint
- Structured JSON response
- CrewAI framework metadata

---

## 15. Container Run Option

Yes, this application can run as a container.

The app supports two Docker patterns:

- **Recommended full local stack:** Streamlit + FastAPI + Ollama all run through Docker Compose.
- **Lightweight development stack:** Streamlit + FastAPI run in Docker while Ollama keeps running directly on your Mac.

Ollama is not copied into the FastAPI application image. It runs as a separate runtime service, which is the better production-style design because the model server and app server can be scaled, upgraded, and monitored independently.

### 15.1 Prerequisites

Install Docker Desktop first:

```bash
docker --version
docker compose version
```

If those commands fail, install Docker Desktop from:

```text
https://www.docker.com/products/docker-desktop/
```

### 15.2 Run Full App With Containerized Ollama

This is the easiest production-style local run.

From the project folder:

```bash
cd enterprise_ai_resume_generator_crewai
docker compose up --build
```

This starts:

- Ollama container with persistent model storage
- One-time model pull container for `llama3.2`
- FastAPI backend on port `8000`
- Streamlit frontend on port `8501`

Open:

```text
http://127.0.0.1:8501
```

Login token for local development:

```text
dev-secret-key
```

API docs:

```text
http://127.0.0.1:8000/docs
```

The Ollama container is exposed on host port `11435` to avoid conflicting with a Mac Ollama process already using `11434`:

```text
http://127.0.0.1:11435
```

Inside Docker, the API calls Ollama through:

```text
http://ollama:11434
```

Stop containers:

```bash
docker compose down
```

Remove the persisted Ollama model volume only if you want to delete downloaded models:

```bash
docker compose down -v
```

### 15.3 Optional: Use Ollama Running On Your Mac

If you do not want Ollama containerized, keep Ollama running on your Mac and point the API container to:

```text
http://host.docker.internal:11434
```

Start Ollama on the host machine:

```bash
ollama serve
ollama pull llama3.2
```

If `ollama serve` says port `11434` is already in use, Ollama is already running.

Then edit `docker-compose.yml` and set the API environment variable back to:

```yaml
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### 15.4 Build Docker Image Manually

```bash
docker build -t enterprise-ai-resume-generator-crewai .
```

### 15.5 Run API Container Only

```bash
docker run \
  -p 8000:8000 \
  --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  enterprise-ai-resume-generator-crewai
```

Then open:

```text
http://127.0.0.1:8000/docs
```

### 15.6 Health Checks

After the stack starts, check:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

---

## 16. GitHub Push Instructions

### 16.1 Initialize Git

```bash
git init
git add .
git commit -m "Initial commit - Enterprise AI Resume Generator Agent"
```

### 16.2 Create GitHub repository

Go to GitHub and create a new repository.

Example repository name:

```text
enterprise-ai-resume-generator-agent
```

Do not initialize with another README if this project already has one.

### 16.3 Add remote

```bash
git remote add origin https://github.com/<your-username>/enterprise-ai-resume-generator-agent.git
```

### 16.4 Push to GitHub

```bash
git branch -M main
git push -u origin main
```

---

## 17. GitLab Push Instructions

### 17.1 Initialize Git

```bash
git init
git add .
git commit -m "Initial commit - Enterprise AI Resume Generator Agent"
```

### 17.2 Create GitLab project

Create a blank GitLab project.

Example project name:

```text
enterprise-ai-resume-generator-agent
```

### 17.3 Add remote

```bash
git remote add origin https://gitlab.com/<your-username>/enterprise-ai-resume-generator-agent.git
```

### 17.4 Push to GitLab

```bash
git branch -M main
git push -u origin main
```

---

## 18. Suggested Git Commit History

If you want a clean professional commit history:

```bash
git add .
git commit -m "Create FastAPI backend and Pydantic models"

git add .
git commit -m "Add CrewAI multi-agent resume workflow"

git add .
git commit -m "Integrate Ollama local LLM runtime"

git add .
git commit -m "Add Streamlit frontend"

git add .
git commit -m "Add tests, Docker, and documentation"
```

For a class project, one commit is also acceptable.

---

## 19. What to Submit

Submit one or more of the following based on your instructor’s requirement:

- GitHub or GitLab repository link
- ZIP file
- Screenshots
- README
- Project summary

Recommended screenshots:

1. GitHub/GitLab repository page
2. Streamlit UI running at `localhost:8501`
3. Swagger UI at `localhost:8000/docs`
4. Successful `/health` response
5. Successful resume generation response
6. Terminal showing `pytest` passing
7. Terminal showing Ollama model installed or running

---

## 20. Demo Walkthrough

Use this sequence:

1. Start Ollama

```bash
ollama serve
```

2. Start FastAPI

```bash
uvicorn app.main:app --reload
```

3. Start Streamlit

```bash
streamlit run frontend/streamlit_app.py
```

4. Open Streamlit

```text
http://localhost:8501
```

5. Fill candidate and job fields.

6. Click **Generate Resume**.

7. Show:

- Agentic framework = CrewAI
- LLM provider = Ollama
- Crew execution path
- ATS score
- Generated resume content
- Reviewer output

8. Open FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

9. Show tests:

```bash
pytest
```

---

## 21. Troubleshooting

### Issue: Ollama not responding

Check if Ollama is running:

```bash
ollama list
```

Start Ollama:

```bash
ollama serve
```

### Issue: Model not found

Pull the model:

```bash
ollama pull llama3.2
```

### Issue: Streamlit cannot call API

Make sure FastAPI is running:

```bash
uvicorn app.main:app --reload
```

Check `.env`:

```text
FASTAPI_BASE_URL=http://127.0.0.1:8000
```

### Issue: Unauthorized API request

Make sure header is correct:

```text
X-API-Key: dev-secret-key
```

### Issue: CrewAI is slow

Use a smaller Ollama model:

```bash
ollama pull phi3
```

Update `.env`:

```text
OLLAMA_MODEL=phi3
```

### Issue: Python dependency problems

Use Python 3.10, 3.11, or 3.12 if possible.

Then reinstall:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 22. Production Engineering Features

This project includes:

- API-based architecture
- Authentication layer
- Multi-agent orchestration
- Local LLM integration
- Structured JSON response
- Logging
- Metrics endpoint
- Frontend/backend separation
- Automated tests
- Docker support
- Environment-based configuration
- Git-ready structure

---

## 23. Final Project Summary

This project demonstrates an enterprise-style AI workflow using:

```text
CrewAI + Ollama + FastAPI + Streamlit
```

It satisfies the assignment requirement by implementing:

```text
User/API Request
        ↓
FastAPI Endpoint
        ↓
Authentication Layer
        ↓
Orchestrator
   ├── Profile Analyzer Agent
   ├── ATS Optimization Agent
   ├── Resume Writer Agent
   ├── Reviewer Agent
        ↓
Structured JSON Response
        ↓
Logs + Monitoring
```

The system is secure, testable, observable, locally runnable, and ready to push to GitHub or GitLab.
