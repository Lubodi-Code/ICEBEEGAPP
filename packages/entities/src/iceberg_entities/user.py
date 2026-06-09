"""USER — la persona dueña del iceberg."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from iceberg_entities.iceberg import Iceberg


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    nombre: str
    creado: datetime = Field(default_factory=lambda: datetime.now(UTC))

    icebergs: list["Iceberg"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )
