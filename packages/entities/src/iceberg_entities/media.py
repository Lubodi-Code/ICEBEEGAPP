"""MEDIA — la multimedia de una entrada (imagen o video)."""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from iceberg_entities.entry import Entry


class Media(SQLModel, table=True):
    __tablename__ = "media"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    entry_id: str = Field(foreign_key="entries.id", ondelete="CASCADE", index=True)
    url: str
    tipo: str  # "image" | "video"
    orden: int = Field(default=0)

    entry: "Entry" = Relationship(back_populates="media")
