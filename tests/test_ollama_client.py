import requests

from app.services.ollama_client import OllamaClient


def test_crewai_llm_name_uses_ollama_prefix():
    client = OllamaClient()

    assert client.crewai_llm_name().startswith("ollama/")


def test_generate_returns_response_text(monkeypatch):
    client = OllamaClient()

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "  generated resume text  "}

    def fake_post(url, json, timeout):
        assert url == f"{client.base_url}/api/generate"
        assert json["model"] == client.model
        assert json["stream"] is False
        assert json["system"] == "system prompt"
        assert timeout == client.timeout
        return Response()

    monkeypatch.setattr(requests, "post", fake_post)

    assert client.generate("prompt", system="system prompt") == "generated resume text"


def test_generate_returns_none_when_ollama_request_fails(monkeypatch):
    client = OllamaClient()

    def fake_post(url, json, timeout):
        raise requests.RequestException("connection failed")

    monkeypatch.setattr(requests, "post", fake_post)

    assert client.generate("prompt") is None


def test_is_available_returns_true_when_tags_endpoint_responds(monkeypatch):
    client = OllamaClient()

    class Response:
        def raise_for_status(self):
            return None

    def fake_get(url, timeout):
        assert url == f"{client.base_url}/api/tags"
        assert timeout <= 5
        return Response()

    monkeypatch.setattr(requests, "get", fake_get)

    assert client.is_available() is True


def test_is_available_returns_false_when_tags_endpoint_fails(monkeypatch):
    client = OllamaClient()

    def fake_get(url, timeout):
        raise requests.RequestException("connection failed")

    monkeypatch.setattr(requests, "get", fake_get)

    assert client.is_available() is False
