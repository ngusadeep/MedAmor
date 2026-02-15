"""Application configuration from environment."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def _root_env_path() -> Path:
    """Repo root (parent of backend/). Used so backend loads root .env."""
    return Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Settings loaded from root .env; see repo root .env.example."""

    _env_path = _root_env_path()
    model_config = SettingsConfigDict(
        env_file=[str(_env_path)] if _env_path.exists() else [],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (PostgreSQL only)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/medaudit"

    # EHR mock data root (project root; contains EHR-DATA_* folders). Set EHR_DATA_ROOT in Docker.
    ehr_data_root: str | None = None

    @property
    def ehr_data_root_resolved(self) -> Path:
        if self.ehr_data_root:
            return Path(self.ehr_data_root)
        return Path(__file__).resolve().parents[3]

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # ChromaDB (vector DB for RAG)
    chroma_persist_dir: str = "./chroma_data"

    # Embedding: "openai" uses OpenAI text-embedding-3-small when openai_api_key set; else FastEmbed (bge-small)
    embedding_provider: str = "fastembed"  # "fastembed" | "openai"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    # Legacy Qdrant (optional; RAG uses ChromaDB when chroma_persist_dir is set)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # Redis / Celery (use redis for broker when available)
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ / Celery (use CELERY_BROKER_URL=redis://... for Redis)
    celery_broker_url: str = "amqp://guest:guest@localhost:5672/"
    celery_result_backend: str | None = None  # e.g. redis://localhost:6379/0 when using Redis broker

    # JWT
    jwt_secret_key: str = "change_me_jwt_secret_min_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Hugging Face (MedGemma)
    hf_token: str | None = None
    hf_medgemma_endpoint: str | None = None

    # Medical KB path (for RAG indexing); default repo docs/Medical_KB
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
