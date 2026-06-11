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

    # URL base del frontend (SPA). La usa la intro del video para sacar una
    # screenshot real del editor (modo mapa) con Playwright; si no está
    # disponible, el render cae al mapa dibujado con Pillow.
    frontend_base_url: str = "http://localhost:5173"

    # Cloudflare R2 (S3-compatible). Vacío => storage usa fallback local.
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_public_url: str = ""

    # Límite de tamaño para videos subidos (MB).
    max_video_mb: int = 25

    # Límite de tamaño para música subida a un nivel (MB).
    max_audio_mb: int = 15

    # Vigencia (días) de los tokens de edición compartibles.
    edit_token_expiry_days: int = 30

    # Pipeline de video: motor TTS ("edge" | "espeak" | "piper" | "silent").
    tts_engine: str = "edge"
    edge_voice: str = "es-ES-AlvaroNeural"  # voz neuronal tipo Loquendo moderno
    edge_rate: str = "+0%"  # velocidad, ej. "+10%" / "-5%"
    espeak_voice: str = "es"
    espeak_speed: int = 165
    piper_voice: str = ""  # ruta al modelo de voz .onnx de Piper

    # Render: relación de aspecto ("9:16" | "16:9") y fps de salida.
    video_aspect: str = "9:16"
    video_fps: int = 24

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
