"""ShareService: arma la URL pública y los metadatos Open Graph (el gancho)."""

from __future__ import annotations

from iceberg_accesodatos.config import get_settings
from iceberg_dto import IcebergRead


class ShareService:
    def __init__(self, public_base_url: str | None = None) -> None:
        self._base = (public_base_url or get_settings().public_base_url).rstrip("/")

    def build_url(self, slug: str) -> str:
        return f"{self._base}/i/{slug}"

    def build_og_meta(self, ice: IcebergRead) -> dict:
        """Metadatos para la tarjeta de vista previa al compartir el enlace."""
        n_niveles = len(ice.levels)
        description = f"Un iceberg de curiosidades con {n_niveles} niveles. ¡Explóralo!"
        return {
            "title": ice.titulo,
            "description": description,
            "image": ice.imagen_base or "",
            "url": self.build_url(ice.slug),
        }
