"""Configuración por entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lee la configuración desde variables de entorno y/o un archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos. SQLite por defecto para correr 100% offline en dev.
    database_url: str = "sqlite:///./dev.db"

    # URL pública base (slugs compartibles, OG tags, fallback de media local).
    public_base_url: str = "http://localhost:8000"

    # Cloudflare R2 (S3-compatible). Vacío => storage usa fallback local.
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_public_url: str = ""

    # Límite de tamaño para videos subidos (MB).
    max_video_mb: int = 25

    @property
    def normalized_database_url(self) -> str:
        """Usa el driver psycopg3 para URLs Postgres planas (Neon entrega ``postgresql://``)."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @property
    def r2_enabled(self) -> bool:
        return bool(
            self.r2_account_id
            and self.r2_access_key_id
            and self.r2_secret_access_key
            and self.r2_bucket
        )


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado (un único objeto por proceso)."""
    return Settings()
