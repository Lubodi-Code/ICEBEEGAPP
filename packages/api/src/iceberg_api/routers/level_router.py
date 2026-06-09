"""Router de LEVEL."""

from __future__ import annotations

from fastapi import APIRouter, status

from iceberg_api.deps import LevelServiceDep
from iceberg_dto import LevelCreate, LevelRead, LevelReorder, LevelUpdate

router = APIRouter(tags=["levels"])


@router.post(
    "/icebergs/{iceberg_id}/levels",
    response_model=LevelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_level(iceberg_id: str, data: LevelCreate, service: LevelServiceDep) -> LevelRead:
    return service.add(iceberg_id, data)


@router.post("/levels/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_levels(data: LevelReorder, service: LevelServiceDep) -> None:
    service.reorder(data)


@router.patch("/levels/{id}", response_model=LevelRead)
def update_level(id: str, data: LevelUpdate, service: LevelServiceDep) -> LevelRead:
    return service.update(id, data)


@router.delete("/levels/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_level(id: str, service: LevelServiceDep) -> None:
    service.remove(id)
