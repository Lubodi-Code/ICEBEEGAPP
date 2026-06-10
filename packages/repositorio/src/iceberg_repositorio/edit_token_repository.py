"""Repositorio de EDIT_TOKEN."""

from __future__ import annotations

from sqlmodel import select

from iceberg_entities import EditToken
from iceberg_repositorio.base import BaseRepository


class EditTokenRepository(BaseRepository[EditToken]):
    model = EditToken

    def find_by_hash(self, iceberg_id: str, token_hash: str) -> EditToken | None:
        stmt = select(EditToken).where(
            EditToken.iceberg_id == iceberg_id,
            EditToken.token_hash == token_hash,
        )
        return self.session.exec(stmt).first()
