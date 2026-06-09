"""Repositorio de LEVEL."""

from __future__ import annotations

from sqlmodel import Session, select

from iceberg_entities import Level
from iceberg_repositorio.base import BaseRepository


class LevelRepository(BaseRepository[Level]):
    model = Level

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_by_iceberg(self, iceberg_id: str) -> list[Level]:
        stmt = select(Level).where(Level.iceberg_id == iceberg_id).order_by(Level.orden)
        return list(self.session.exec(stmt).all())
