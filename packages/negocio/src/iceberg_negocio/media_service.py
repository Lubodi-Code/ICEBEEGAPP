"""Servicio de MEDIA: comprime imágenes a WebP y sube a R2 (o fallback local)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image

from iceberg_accesodatos.config import get_settings
from iceberg_dto import MediaRead
from iceberg_entities import Media
from iceberg_negocio.errors import ValidationError
from iceberg_negocio.storage import R2Storage
from iceberg_repositorio import MediaRepository

MAX_IMAGE_SIDE = 1080
WEBP_QUALITY = 80


class MediaService:
    def __init__(self, repo: MediaRepository, storage: R2Storage) -> None:
        self.repo = repo
        self.storage = storage

    def upload(
        self,
        entry_id: str,
        filename: str,
        content_type: str,
        raw: bytes,
    ) -> MediaRead:
        content_type = (content_type or "").lower()
        orden = len(self.repo.list_by_entry(entry_id))

        if content_type.startswith("image/"):
            data = self.compress_webp(raw)
            key = f"{entry_id}/{uuid4().hex}.webp"
            url = self.storage.put(key, data, "image/webp")
            tipo = "image"
        elif content_type.startswith("video/"):
            max_bytes = get_settings().max_video_mb * 1024 * 1024
            if len(raw) > max_bytes:
                raise ValidationError(
                    f"El video supera el máximo de {get_settings().max_video_mb} MB"
                )
            ext = Path(filename).suffix or ".mp4"
            key = f"{entry_id}/{uuid4().hex}{ext}"
            url = self.storage.put(key, raw, content_type)
            tipo = "video"
        else:
            raise ValidationError(f"Tipo de archivo no soportado: {content_type!r}")

        media = self.repo.create(Media(entry_id=entry_id, url=url, tipo=tipo, orden=orden))
        return MediaRead.model_validate(media)

    def upload_audio(self, level_id: str, filename: str, content_type: str, raw: bytes) -> str:
        """Sube un archivo de audio (música de nivel) y devuelve su URL pública."""
        content_type = (content_type or "").lower()
        if not content_type.startswith("audio/"):
            raise ValidationError(f"Se esperaba un archivo de audio, llegó: {content_type!r}")
        max_bytes = get_settings().max_audio_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise ValidationError(f"El audio supera el máximo de {get_settings().max_audio_mb} MB")
        ext = Path(filename).suffix or ".mp3"
        key = f"music/{level_id}/{uuid4().hex}{ext}"
        return self.storage.put(key, raw, content_type)

    def compress_webp(self, raw: bytes) -> bytes:
        """Convierte a RGB, limita el lado mayor a 1080px, calidad 80, sin EXIF."""
        with Image.open(BytesIO(raw)) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            out = BytesIO()
            # Sin pasar exif => los metadatos EXIF se descartan.
            img.save(out, format="WEBP", quality=WEBP_QUALITY)
        return out.getvalue()
