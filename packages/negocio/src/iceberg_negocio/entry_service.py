"""Servicio de ENTRY."""

from __future__ import annotations

from iceberg_dto import EntryCreate, EntryRead, EntryUpdate
from iceberg_entities import Entry
from iceberg_negocio.errors import NotFoundError
from iceberg_repositorio import EntryRepository


class EntryService:
    def __init__(self, repo: EntryRepository) -> None:
        self.repo = repo

    def add(self, level_id: str, data: EntryCreate) -> EntryRead:
        entry = Entry(
            level_id=level_id,
            titulo=data.titulo,
            descripcion=data.descripcion,
            orden=data.orden,
        )
        entry = self.repo.create(entry)
        return EntryRead.model_validate(entry)

    def edit(self, id: str, data: EntryUpdate) -> EntryRead:
        entry = self.repo.get(id)
        if entry is None:
            raise NotFoundError(f"Entry {id} no existe")
        if data.titulo is not None:
            entry.titulo = data.titulo
        if data.descripcion is not None:
            entry.descripcion = data.descripcion
        if data.orden is not None:
            entry.orden = data.orden
        entry = self.repo.update(entry)
        return EntryRead.model_validate(entry)

    def remove(self, id: str) -> None:
        if self.repo.get(id) is None:
            raise NotFoundError(f"Entry {id} no existe")
        self.repo.delete(id)
