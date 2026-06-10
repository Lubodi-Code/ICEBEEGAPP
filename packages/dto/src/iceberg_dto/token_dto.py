"""DTOs de EDIT_TOKEN (enlace de edición compartible)."""

from __future__ import annotations

from pydantic import BaseModel


class EditTokenRead(BaseModel):
    token: str  # token en claro; solo se devuelve al crearlo
    expires_at: str  # ISO-8601


class EditTokenValidation(BaseModel):
    valid: bool
