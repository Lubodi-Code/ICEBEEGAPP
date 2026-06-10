"""Router de VIDEO: genera el .mp4 efímero y lo sirve como descarga."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from iceberg_api.deps import VideoServiceDep
from iceberg_dto import VideoRequest

router = APIRouter(tags=["video"])


def _cleanup(path: str) -> None:
    """Borra el .mp4 (y su directorio temporal) una vez enviada la respuesta."""
    shutil.rmtree(Path(path).parent, ignore_errors=True)


@router.post("/video")
def generate_video(req: VideoRequest, service: VideoServiceDep) -> FileResponse:
    path = service.generate(req)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename="iceberg.mp4",
        background=BackgroundTask(_cleanup, path),
    )
