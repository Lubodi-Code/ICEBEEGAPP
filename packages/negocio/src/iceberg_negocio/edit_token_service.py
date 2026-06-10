"""Servicio de EDIT_TOKEN: crea y valida tokens de edición compartibles.

El token en claro solo se devuelve al crearlo; en la base se guarda su SHA-256.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_dto import EditTokenRead, EditTokenValidation
from iceberg_entities import EditToken
from iceberg_repositorio import EditTokenRepository


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class EditTokenService:
    def __init__(self, repo: EditTokenRepository, settings: Settings | None = None) -> None:
        self.repo = repo
        self._settings = settings or get_settings()

    def create(self, iceberg_id: str) -> EditTokenRead:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.edit_token_expiry_days)
        self.repo.create(
            EditToken(iceberg_id=iceberg_id, token_hash=_hash(token), expires_at=expires_at)
        )
        return EditTokenRead(token=token, expires_at=expires_at.isoformat())

    def validate(self, iceberg_id: str, token: str) -> EditTokenValidation:
        et = self.repo.find_by_hash(iceberg_id, _hash(token))
        if et is None:
            return EditTokenValidation(valid=False)
        expires = et.expires_at if et.expires_at.tzinfo else et.expires_at.replace(tzinfo=UTC)
        return EditTokenValidation(valid=expires > datetime.now(UTC))
