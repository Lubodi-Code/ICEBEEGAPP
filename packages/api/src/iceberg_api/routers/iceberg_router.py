"""Router de ICEBERG."""

from __future__ import annotations

from fastapi import APIRouter, status

from iceberg_api.deps import IcebergServiceDep
from iceberg_dto import IcebergCreate, IcebergRead, IcebergUpdate

router = APIRouter(tags=["icebergs"])


@router.post("/icebergs", response_model=IcebergRead, status_code=status.HTTP_201_CREATED)
def create_iceberg(data: IcebergCreate, service: IcebergServiceDep) -> IcebergRead:
    return service.create(data)


@router.get("/icebergs/{slug}", response_model=IcebergRead)
def get_iceberg(slug: str, service: IcebergServiceDep) -> IcebergRead:
    return service.get_public(slug)


@router.patch("/icebergs/{id}", response_model=IcebergRead)
def update_iceberg(id: str, data: IcebergUpdate, service: IcebergServiceDep) -> IcebergRead:
    return service.update(id, data)


@router.delete("/icebergs/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_iceberg(id: str, service: IcebergServiceDep) -> None:
    service.delete(id)
