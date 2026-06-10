"""DTOs del pipeline de video."""

from __future__ import annotations

from pydantic import BaseModel, Field

from iceberg_dto.entry_dto import DESCRIPCION_MAX


class MediaRef(BaseModel):
    url: str
    tipo: str  # "image" | "video"


class LevelRef(BaseModel):
    """Nivel del iceberg para la intro con mapa de niveles (vista lejana + zoom)."""

    numero: int
    nombre: str | None = None


class VideoRequest(BaseModel):
    iceberg_title: str = Field(max_length=120)
    level_number: int
    level_name: str | None = None
    entry_title: str = Field(max_length=160)
    description: str = Field(max_length=DESCRIPCION_MAX)
    media: list[MediaRef] = []
    levels: list[LevelRef] = []  # todos los niveles, en orden; para la intro con zoom
    music_url: str | None = None  # música de fondo (se mezcla bajo la narración)
    show_url: bool = False  # mostrar la URL pública en el outro
