"""ICEBERG — el tablero del iceberg."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from iceberg_entities.level import Level
    from iceberg_entities.user import User


class Iceberg(SQLModel, table=True):
    __tablename__ = "icebergs"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: str = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    titulo: str
    slug: str = Field(unique=True, index=True)
    imagen_base: str | None = Field(default=None)
    creado: datetime = Field(default_factory=lambda: datetime.now(UTC))

    owner: "User" = Relationship(back_populates="icebergs")
    levels: list["Level"] = Relationship(
        back_populates="iceberg",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Level.orden"},
    )
