"""Servicio de LEVEL."""

from __future__ import annotations

from iceberg_dto import LevelCreate, LevelRead, LevelReorder, LevelUpdate
from iceberg_entities import Level
from iceberg_negocio.errors import NotFoundError
from iceberg_repositorio import LevelRepository


class LevelService:
    def __init__(self, repo: LevelRepository) -> None:
        self.repo = repo

    def add(self, iceberg_id: str, data: LevelCreate) -> LevelRead:
        level = Level(
            iceberg_id=iceberg_id,
            numero=data.numero,
            nombre=data.nombre,
            orden=data.orden,
        )
        level = self.repo.create(level)
        return LevelRead.model_validate(level)

    def update(self, id: str, data: LevelUpdate) -> LevelRead:
        level = self.repo.get(id)
        if level is None:
            raise NotFoundError(f"Level {id} no existe")
        if data.numero is not None:
            level.numero = data.numero
        if data.nombre is not None:
            level.nombre = data.nombre
        if data.orden is not None:
            level.orden = data.orden
        if data.music_url is not None:
            level.music_url = data.music_url or None  # "" limpia la música
        level = self.repo.update(level)
        return LevelRead.model_validate(level)

    def remove(self, id: str) -> None:
        if self.repo.get(id) is None:
            raise NotFoundError(f"Level {id} no existe")
        self.repo.delete(id)

    def reorder(self, data: LevelReorder) -> None:
        """Asigna ``orden`` según la posición en ``level_ids``."""
        for posicion, level_id in enumerate(data.level_ids):
            level = self.repo.get(level_id)
            if level is None:
                raise NotFoundError(f"Level {level_id} no existe")
            level.orden = posicion
            self.repo.update(level)
