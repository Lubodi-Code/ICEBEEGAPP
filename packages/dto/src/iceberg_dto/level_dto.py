"""DTOs de LEVEL."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from iceberg_dto.entry_dto import EntryRead


class LevelCreate(BaseModel):
    numero: int = Field(ge=1)
    nombre: str | None = None
    orden: int = 0


class LevelUpdate(BaseModel):
    numero: int | None = Field(default=None, ge=1)
    nombre: str | None = None
    orden: int | None = None
    music_url: str | None = None  # "" para quitar la música del nivel


class LevelReorder(BaseModel):
    level_ids: list[str]  # nuevo orden (UUIDs como str)


class LevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    numero: int
    nombre: str | None
    orden: int
    music_url: str | None = None
    entries: list[EntryRead] = []
