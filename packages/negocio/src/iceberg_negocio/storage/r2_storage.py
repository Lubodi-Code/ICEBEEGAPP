"""Adaptador de object storage hacia Cloudflare R2 (API compatible S3).

Si hay credenciales R2 configuradas usa boto3. Si NO las hay (dev), cae a un
fallback que guarda en ``./media_local/{key}`` y devuelve una URL servida por
la propia API, de modo que el proyecto corre 100% offline.
"""

from __future__ import annotations

from pathlib import Path

from iceberg_accesodatos.config import Settings, get_settings

LOCAL_MEDIA_DIR = Path("media_local")


class R2Storage:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None
        if self._settings.r2_enabled:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{self._settings.r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self._settings.r2_access_key_id,
                aws_secret_access_key=self._settings.r2_secret_access_key,
                region_name="auto",
            )

    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Sube ``data`` bajo ``key`` y devuelve la URL pública."""
        if self._client is not None:
            self._client.put_object(
                Bucket=self._settings.r2_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            base = self._settings.r2_public_url.rstrip("/")
            return f"{base}/{key}"

        # Fallback local (dev): escribe en ./media_local/{key}.
        dest = LOCAL_MEDIA_DIR / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        base = self._settings.public_base_url.rstrip("/")
        return f"{base}/media_local/{key}"

    def get(self, key: str) -> bytes:
        """Descarga el contenido almacenado bajo ``key``."""
        if self._client is not None:
            resp = self._client.get_object(Bucket=self._settings.r2_bucket, Key=key)
            return resp["Body"].read()

        return (LOCAL_MEDIA_DIR / key).read_bytes()
