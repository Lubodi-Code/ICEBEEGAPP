"""MediaFetcher — trae la multimedia de la entrada a disco local.

Resuelve cada ``MediaRef`` según su origen:

- URL bajo ``R2_PUBLIC_URL`` o bajo ``/media_local/`` → lee vía ``R2Storage.get``
  (R2 o fallback local), sin depender de que el bucket sea públicamente legible.
- Cualquier otra URL http(s) → descarga directa.

Los assets que fallan se omiten (el video puede generarse sin multimedia).
"""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_dto import MediaRef
from iceberg_negocio.storage import R2Storage


class MediaFetcher:
    def __init__(self, storage: R2Storage | None = None, settings: Settings | None = None) -> None:
        self._storage = storage or R2Storage()
        self._settings = settings or get_settings()

    def fetch(self, media: list[MediaRef], workdir: str | None = None) -> list[str]:
        """Descarga imágenes y clips y devuelve sus rutas locales (en orden)."""
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_media_"))
        out_dir.mkdir(parents=True, exist_ok=True)

        paths: list[str] = []
        for i, ref in enumerate(media):
            try:
                data = self._read(ref.url)
            except Exception:
                continue  # asset inaccesible: la escena se arma con los demás
            suffix = Path(urlparse(ref.url).path).suffix or (
                ".webp" if ref.tipo == "image" else ".mp4"
            )
            dest = out_dir / f"asset_{i}{suffix}"
            dest.write_bytes(data)
            paths.append(str(dest))
        return paths

    def fetch_audio(self, url: str, workdir: str) -> str | None:
        """Descarga un audio (música) y devuelve su ruta local, o None si falla."""
        try:
            data = self._read(url)
        except Exception:
            return None
        suffix = Path(urlparse(url).path).suffix or ".mp3"
        dest = Path(workdir) / f"music{suffix}"
        dest.write_bytes(data)
        return str(dest)

    def _read(self, url: str) -> bytes:
        key = self._extract_key(url)
        if key is not None:
            return self._storage.get(key)
        if url.startswith(("http://", "https://")):
            with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
                return resp.read()
        raise ValueError(f"URL de media no soportada: {url!r}")

    def _extract_key(self, url: str) -> str | None:
        """Devuelve la key de storage si la URL apunta a nuestro R2 o al fallback local."""
        r2_base = self._settings.r2_public_url.rstrip("/")
        if r2_base and url.startswith(r2_base + "/"):
            return url[len(r2_base) + 1 :]
        marker = "/media_local/"
        if marker in url:
            return url.split(marker, 1)[1]
        return None
