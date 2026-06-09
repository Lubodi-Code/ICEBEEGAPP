"""DTOs del pipeline de video."""

from __future__ import annotations

from pydantic import BaseModel


class MediaRef(BaseModel):
    url: str
    tipo: str  # "image" | "video"


class VideoRequest(BaseModel):
    iceberg_title: str
    level_number: int
    level_name: str | None = None
    entry_title: str
    description: str
    media: list[MediaRef] = []
