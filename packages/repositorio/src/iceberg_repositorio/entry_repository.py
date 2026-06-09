"""Repositorio de ENTRY."""

from __future__ import annotations

from sqlmodel import Session, select

from iceberg_entities import Entry
from iceberg_repositorio.base import BaseRepository


class EntryRepository(BaseRepository[Entry]):
    model = Entry

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_by_level(self, level_id: str) -> list[Entry]:
        stmt = select(Entry).where(Entry.level_id == level_id).order_by(Entry.orden)
        return list(self.session.exec(stmt).all())
