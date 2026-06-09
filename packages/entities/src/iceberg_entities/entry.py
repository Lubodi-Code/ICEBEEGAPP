"""ENTRY — una curiosidad dentro de un nivel."""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Text as SAText
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from iceberg_entities.level import Level
    from iceberg_entities.media import Media


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    level_id: str = Field(foreign_key="levels.id", ondelete="CASCADE", index=True)
    titulo: str
    descripcion: str = Field(default="", sa_type=SAText)
    orden: int = Field(default=0)

    level: "Level" = Relationship(back_populates="entries")
    media: list["Media"] = Relationship(
        back_populates="entry",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Media.orden"},
    )
