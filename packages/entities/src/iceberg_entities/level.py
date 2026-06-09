"""LEVEL — un nivel de profundidad del iceberg; agrupa varias entradas."""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from iceberg_entities.entry import Entry
    from iceberg_entities.iceberg import Iceberg


class Level(SQLModel, table=True):
    __tablename__ = "levels"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    iceberg_id: str = Field(foreign_key="icebergs.id", ondelete="CASCADE", index=True)
    numero: int
    nombre: str | None = Field(default=None)
    orden: int = Field(default=0)

    iceberg: "Iceberg" = Relationship(back_populates="levels")
    entries: list["Entry"] = Relationship(
        back_populates="level",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Entry.orden"},
    )
