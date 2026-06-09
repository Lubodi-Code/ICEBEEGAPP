"""Router de VIDEO (pipeline aún no implementado)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from iceberg_dto import VideoRequest

router = APIRouter(tags=["video"])


@router.post("/video")
def generate_video(req: VideoRequest) -> None:
    # TODO: invocar VideoService.generate(req) y devolver StreamingResponse (.mp4) efímero.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Pipeline de video aún no implementado",
    )
