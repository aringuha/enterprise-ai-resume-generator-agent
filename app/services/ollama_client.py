import logging
from typing import Optional
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def provider_name(self) -> str:
        return f"Ollama local LLM ({self.model})" if settings.use_ollama else "Deterministic fallback"

    def crewai_llm_name(self) -> str:
        return f"ollama/{self.model}"

    def is_available(self) -> bool:
        if not settings.use_ollama:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=min(self.timeout, 5))
            response.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("Ollama readiness check failed. Error: %s", exc)
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        if not settings.use_ollama:
            return None
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }
        if system:
            payload["system"] = system
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as exc:
            logger.warning("Ollama unavailable; using fallback. Error: %s", exc)
            return None

ollama_client = OllamaClient()
