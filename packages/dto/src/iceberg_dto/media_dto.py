"""DTOs de MEDIA."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    tipo: str
    orden: int
