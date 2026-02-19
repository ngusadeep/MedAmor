"""Application configuration from environment.

ALL values MUST be provided via environment variables. No hardcoded defaults.
The backend loads .env from the project root when run locally; in Docker, env vars are set by compose from .env.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _root_env_path() -> Path:
    """Path to project root .env so backend loads all config from that file."""
    return Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """ALL settings from .env (required - no defaults). See .env.example for every variable."""

    _env_path = _root_env_path()
    model_config = SettingsConfigDict(
        env_file=[str(_env_path)] if _env_path.exists() else [],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server (required)
    host: str
    port: int

    # Database (required)
    database_url: str

    # EHR (optional - when not set, uses ehr_data_root_resolved)
    ehr_service_url: str | None = None

    # EHR data root (optional - defaults to project root)
    ehr_data_root: str | None = None

    @property
    def ehr_data_root_resolved(self) -> Path:
        if self.ehr_data_root:
            return Path(self.ehr_data_root)
        return Path(__file__).resolve().parents[3]

    # Environment (required)
    environment: Literal["development", "staging", "production"]
    debug: bool

    # CORS (required)
    allowed_origins: str

    # ChromaDB (required)
    chroma_persist_dir: str

    # Embedding (required)
    embedding_provider: str  # "fastembed" | "openai"
    openai_api_key: str | None = None
    openai_embedding_model: str

    # Legacy Qdrant (optional)
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # Redis / Celery (required)
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str | None = None

    # JWT (required)
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_expire_minutes: int

    # Audit AI provider (required)
    audit_ai_provider: Literal["medgemma", "gemini", "openai"]

    # MedGemma (optional - required when audit_ai_provider=medgemma)
    hf_token: str | None = None
    hf_medgemma_endpoint: str | None = None

    # Google Gemini (optional - required when audit_ai_provider=gemini)
    google_api_key: str | None = None
    gemini_model: str

    # OpenAI audit (required when audit_ai_provider=openai)
    openai_audit_model: str

    # Medical KB path (optional - defaults to docs/Medical_KB)
    medical_kb_path: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def medical_kb_path_resolved(self) -> Path:
        if self.medical_kb_path:
            return Path(self.medical_kb_path)
        return Path(__file__).resolve().parents[3] / "docs" / "Medical_KB"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
