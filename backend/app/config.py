"""Centralized application settings, loaded from environment variables.

Every other module reads configuration from `get_settings()` rather than
calling `os.environ` directly, so tests can override settings by constructing
a `Settings` instance instead of mutating process environment.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+asyncpg://docengine:docengine@localhost:5432/docengine"

    # --- Auth ---
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # --- Uploads ---
    max_upload_bytes: int = 5 * 1024 * 1024  # 5 MB
    storage_dir: str = "./storage/uploads"
    allowed_import_extensions: tuple[str, ...] = (".txt", ".md", ".markdown", ".docx")

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:8000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
