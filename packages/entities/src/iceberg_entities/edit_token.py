"""EDIT_TOKEN — token compartible que habilita editar un iceberg por enlace."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class EditToken(SQLModel, table=True):
    __tablename__ = "edit_tokens"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    iceberg_id: str = Field(foreign_key="icebergs.id", ondelete="CASCADE", index=True)
    token_hash: str = Field(index=True)  # SHA-256 del token; el plano solo se devuelve una vez
    expires_at: datetime
    created_at: datetime = Field(default_factory=_now)
