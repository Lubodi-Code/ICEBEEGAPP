"""DTOs de ENTRY."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from iceberg_dto.media_dto import MediaRead


class EntryCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=160)
    descripcion: str = ""
    orden: int = 0


class EntryUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    descripcion: str | None = None
    orden: int | None = None


class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    titulo: str
    descripcion: str
    orden: int
    media: list[MediaRead] = []
