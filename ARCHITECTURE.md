# Architecture

```text
User
 ↓
Streamlit Frontend
 ↓
FastAPI Backend
 ↓
API Key Authentication
 ↓
ResumeOrchestrator
 ↓
CrewAI Sequential Crew
 ├── Profile Analyzer Agent
 ├── ATS Optimization Agent
 ├── Resume Writer Agent
 └── Reviewer Agent
 ↓
Ollama Local LLM
 ↓
Structured JSON Response
 ↓
Logs and Metrics
```

CrewAI is the agentic framework. Ollama is the local LLM runtime.
