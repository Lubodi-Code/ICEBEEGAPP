"""Dependencias de FastAPI: sesión + servicios de negocio (vía factory DI).

La capa API obtiene la sesión de ``iceberg_accesodatos.get_session`` y delega la
construcción de servicios en ``iceberg_negocio``. No importa repositorios ni
entidades (lo prohíbe el contrato de import-linter).
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from iceberg_accesodatos import get_session
from iceberg_negocio import (
    EditTokenService,
    EntryService,
    IcebergService,
    LevelService,
    MediaService,
    ShareService,
    VideoService,
    get_edit_token_service,
    get_entry_service,
    get_iceberg_service,
    get_level_service,
    get_media_service,
    get_share_service,
    get_video_service,
)


def db_session() -> Generator[Session, None, None]:
    yield from get_session()


SessionDep = Annotated[Session, Depends(db_session)]


def iceberg_service(session: SessionDep) -> IcebergService:
    return get_iceberg_service(session)


def level_service(session: SessionDep) -> LevelService:
    return get_level_service(session)


def entry_service(session: SessionDep) -> EntryService:
    return get_entry_service(session)


def media_service(session: SessionDep) -> MediaService:
    return get_media_service(session)


def share_service() -> ShareService:
    return get_share_service()


def video_service() -> VideoService:
    return get_video_service()


def edit_token_service(session: SessionDep) -> EditTokenService:
    return get_edit_token_service(session)


IcebergServiceDep = Annotated[IcebergService, Depends(iceberg_service)]
LevelServiceDep = Annotated[LevelService, Depends(level_service)]
EntryServiceDep = Annotated[EntryService, Depends(entry_service)]
MediaServiceDep = Annotated[MediaService, Depends(media_service)]
ShareServiceDep = Annotated[ShareService, Depends(share_service)]
VideoServiceDep = Annotated[VideoService, Depends(video_service)]
EditTokenServiceDep = Annotated[EditTokenService, Depends(edit_token_service)]
