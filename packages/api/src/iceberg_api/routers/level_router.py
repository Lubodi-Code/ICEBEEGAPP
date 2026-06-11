"""Router de LEVEL."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from iceberg_api.deps import LevelServiceDep, MediaServiceDep
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


@router.post("/levels/{id}/music", response_model=LevelRead)
async def upload_level_music(
    id: str,
    service: LevelServiceDep,
    media: MediaServiceDep,
    file: Annotated[UploadFile, File()],
) -> LevelRead:
    """Sube un audio y lo configura como música de fondo del nivel."""
    raw = await file.read()
    url = media.upload_audio(
        level_id=id,
        filename=file.filename or "musica",
        content_type=file.content_type or "application/octet-stream",
        raw=raw,
    )
    return service.update(id, LevelUpdate(music_url=url))
