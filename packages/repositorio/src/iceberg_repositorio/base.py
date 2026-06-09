"""Repositorio genérico base. Única capa que toca la base de datos."""

from __future__ import annotations

from sqlmodel import Session, SQLModel, select


class BaseRepository[T: SQLModel]:
    """CRUD genérico sobre una entidad SQLModel. Recibe la ``Session`` por constructor."""

    model: type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def get(self, id: str) -> T | None:
        return self.session.get(self.model, id)

    def list(self) -> list[T]:
        return list(self.session.exec(select(self.model)).all())

    def update(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, id: str) -> None:
        obj = self.session.get(self.model, id)
        if obj is not None:
            self.session.delete(obj)
            self.session.commit()
