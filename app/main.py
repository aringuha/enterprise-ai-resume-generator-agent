from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.middleware import InMemoryRateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from app.services.metrics import metrics_service
from app.services.ollama_client import ollama_client

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    description="Enterprise-grade CrewAI + Ollama + Streamlit + FastAPI resume generator",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(InMemoryRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "agentic_framework": "CrewAI",
        "orchestration_mode": "CrewAI Process.sequential",
        "llm_provider": ollama_client.provider_name(),
        "frontend": "Streamlit",
        "api": "FastAPI",
    }

@app.get("/metrics/json")
def metrics_json():
    return metrics_service.snapshot()

@app.get("/metrics")
def metrics():
    return Response(content=metrics_service.prometheus_snapshot(), media_type="text/plain; version=0.0.4")

@app.get("/ready")
def readiness_check(response: Response):
    ollama_ready = ollama_client.is_available()
    ready = (not settings.use_ollama) or ollama_ready
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if ready else "not_ready",
        "service": settings.app_name,
        "ollama_required": settings.use_ollama,
        "ollama_ready": ollama_ready,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
    }
