from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Enterprise AI Resume Generator Agent"
    environment: str = "local"
    api_key: str = "dev-secret-key"
    bearer_token: str = "dev-secret-key"
    jwt_secret: str = "dev-jwt-secret-change-me-32-bytes-min"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "enterprise-ai-resume-generator"
    log_level: str = "INFO"
    cors_origins: str = "http://127.0.0.1:8501,http://localhost:8501,http://127.0.0.1:8502,http://localhost:8502"
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    use_ollama: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 90
    fastapi_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
