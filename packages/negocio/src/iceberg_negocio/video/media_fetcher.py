"""MediaFetcher — descarga la multimedia de la entrada desde R2 a /tmp (STUB)."""

from __future__ import annotations

from iceberg_dto import MediaRef


class MediaFetcher:
    def fetch(self, media: list[MediaRef]) -> list[str]:
        """Descarga imágenes y clips a /tmp y devuelve sus rutas locales.

        TODO: descargar cada MediaRef (imagen o video) desde R2 hacia /tmp.
        """
        raise NotImplementedError("MediaFetcher.fetch aún no implementado")
