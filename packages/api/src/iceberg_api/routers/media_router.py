"""Router de MEDIA (subida multipart)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from iceberg_api.deps import MediaServiceDep
from iceberg_dto import MediaRead

router = APIRouter(tags=["media"])


@router.post(
    "/entries/{entry_id}/media",
    response_model=MediaRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    entry_id: str,
    service: MediaServiceDep,
    file: Annotated[UploadFile, File()],
) -> MediaRead:
    raw = await file.read()
    return service.upload(
        entry_id=entry_id,
        filename=file.filename or "archivo",
        content_type=file.content_type or "application/octet-stream",
        raw=raw,
    )
