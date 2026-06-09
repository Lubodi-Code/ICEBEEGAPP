"""Repositorio de MEDIA."""

from __future__ import annotations

from sqlmodel import Session, select

from iceberg_entities import Media
from iceberg_repositorio.base import BaseRepository


class MediaRepository(BaseRepository[Media]):
    model = Media

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def list_by_entry(self, entry_id: str) -> list[Media]:
        stmt = select(Media).where(Media.entry_id == entry_id).order_by(Media.orden)
        return list(self.session.exec(stmt).all())
