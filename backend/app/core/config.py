"""Application configuration from environment."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from env; see backend/.env.example."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
