"""DTOs de ICEBERG."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from iceberg_dto.level_dto import LevelRead


class IcebergCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=120)
    imagen_base: str | None = None


class IcebergUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=120)
    imagen_base: str | None = None


class IcebergRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    titulo: str
    slug: str
    imagen_base: str | None
    creado: datetime
    levels: list[LevelRead] = []
