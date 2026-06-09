"""Router de ENTRY."""

from __future__ import annotations

from fastapi import APIRouter, status

from iceberg_api.deps import EntryServiceDep
from iceberg_dto import EntryCreate, EntryRead, EntryUpdate

router = APIRouter(tags=["entries"])


@router.post(
    "/levels/{level_id}/entries",
    response_model=EntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entry(level_id: str, data: EntryCreate, service: EntryServiceDep) -> EntryRead:
    return service.add(level_id, data)


@router.patch("/entries/{id}", response_model=EntryRead)
def update_entry(id: str, data: EntryUpdate, service: EntryServiceDep) -> EntryRead:
    return service.edit(id, data)


@router.delete("/entries/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(id: str, service: EntryServiceDep) -> None:
    service.remove(id)
