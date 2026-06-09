"""Repositorio de ICEBERG."""

from __future__ import annotations

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from iceberg_entities import Entry, Iceberg, Level
from iceberg_repositorio.base import BaseRepository


class IcebergRepository(BaseRepository[Iceberg]):
    model = Iceberg

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_slug(self, slug: str) -> Iceberg | None:
        return self.session.exec(select(Iceberg).where(Iceberg.slug == slug)).first()

    def list_by_owner(self, owner_id: str) -> list[Iceberg]:
        stmt = select(Iceberg).where(Iceberg.owner_id == owner_id)
        return list(self.session.exec(stmt).all())

    def get_with_graph(self, slug: str) -> Iceberg | None:
        """Carga el iceberg con todo su grafo: levels -> entries -> media."""
        stmt = (
            select(Iceberg)
            .where(Iceberg.slug == slug)
            .options(
                selectinload(Iceberg.levels)  # type: ignore[arg-type]
                .selectinload(Level.entries)
                .selectinload(Entry.media)
            )
        )
        return self.session.exec(stmt).first()
