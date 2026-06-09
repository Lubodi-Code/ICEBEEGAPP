"""Servicio de ICEBERG: lógica de negocio + mapeo entity <-> dto."""

from __future__ import annotations

import secrets

from slugify import slugify
from sqlmodel import select

from iceberg_dto import IcebergCreate, IcebergRead, IcebergUpdate
from iceberg_entities import Iceberg, User
from iceberg_negocio.errors import NotFoundError
from iceberg_repositorio import IcebergRepository

ANON_USER_NAME = "anon"


class IcebergService:
    def __init__(self, repo: IcebergRepository) -> None:
        self.repo = repo

    # --- comandos -----------------------------------------------------------

    def create(self, data: IcebergCreate, owner_id: str | None = None) -> IcebergRead:
        if owner_id is None:
            owner_id = self._ensure_anon_owner()
        iceberg = Iceberg(
            owner_id=owner_id,
            titulo=data.titulo,
            slug=self.generate_slug(data.titulo),
            imagen_base=data.imagen_base,
        )
        iceberg = self.repo.create(iceberg)
        return IcebergRead.model_validate(iceberg)

    def update(self, id: str, data: IcebergUpdate) -> IcebergRead:
        iceberg = self.repo.get(id)
        if iceberg is None:
            raise NotFoundError(f"Iceberg {id} no existe")
        if data.titulo is not None:
            iceberg.titulo = data.titulo
        if data.imagen_base is not None:
            iceberg.imagen_base = data.imagen_base
        iceberg = self.repo.update(iceberg)
        return IcebergRead.model_validate(iceberg)

    def delete(self, id: str) -> None:
        if self.repo.get(id) is None:
            raise NotFoundError(f"Iceberg {id} no existe")
        self.repo.delete(id)

    # --- consultas ----------------------------------------------------------

    def get_public(self, slug: str) -> IcebergRead:
        iceberg = self.repo.get_with_graph(slug)
        if iceberg is None:
            raise NotFoundError(f"Iceberg con slug '{slug}' no existe")
        return IcebergRead.model_validate(iceberg)

    # --- helpers ------------------------------------------------------------

    def generate_slug(self, titulo: str) -> str:
        """slugify + sufijo corto aleatorio si choca (garantiza unicidad)."""
        base = slugify(titulo) or "iceberg"
        slug = base
        while self.repo.get_by_slug(slug) is not None:
            slug = f"{base}-{secrets.token_hex(3)}"
        return slug

    def _ensure_anon_owner(self) -> str:
        """Obtiene (o crea) el usuario anónimo dueño por defecto del MVP."""
        session = self.repo.session
        user = session.exec(select(User).where(User.nombre == ANON_USER_NAME)).first()
        if user is None:
            user = User(nombre=ANON_USER_NAME)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user.id
