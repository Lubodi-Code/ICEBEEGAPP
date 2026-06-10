"""DTOs del pipeline de video."""

from __future__ import annotations

from pydantic import BaseModel, Field

from iceberg_dto.entry_dto import DESCRIPCION_MAX


class MediaRef(BaseModel):
    url: str
    tipo: str  # "image" | "video"


class VideoRequest(BaseModel):
    iceberg_title: str = Field(max_length=120)
    level_number: int
    level_name: str | None = None
    entry_title: str = Field(max_length=160)
    description: str = Field(max_length=DESCRIPCION_MAX)
    media: list[MediaRef] = []
