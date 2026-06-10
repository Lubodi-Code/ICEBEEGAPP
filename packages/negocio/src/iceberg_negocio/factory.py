"""Factory de inyección de dependencias: arma repo + service para cada entidad."""

from __future__ import annotations

from sqlmodel import Session

from iceberg_negocio.entry_service import EntryService
from iceberg_negocio.iceberg_service import IcebergService
from iceberg_negocio.level_service import LevelService
from iceberg_negocio.media_service import MediaService
from iceberg_negocio.share_service import ShareService
from iceberg_negocio.storage import R2Storage
from iceberg_negocio.video import (
    MediaFetcher,
    NarrationBuilder,
    SceneBuilder,
    TTSEngine,
    VideoRenderer,
    VideoService,
)
from iceberg_repositorio import (
    EntryRepository,
    IcebergRepository,
    LevelRepository,
    MediaRepository,
)


def get_iceberg_service(session: Session) -> IcebergService:
    return IcebergService(IcebergRepository(session))


def get_level_service(session: Session) -> LevelService:
    return LevelService(LevelRepository(session))


def get_entry_service(session: Session) -> EntryService:
    return EntryService(EntryRepository(session))


def get_media_service(session: Session) -> MediaService:
    return MediaService(MediaRepository(session), R2Storage())


def get_share_service() -> ShareService:
    return ShareService()


def get_video_service() -> VideoService:
    return VideoService(
        narration=NarrationBuilder(),
        tts=TTSEngine(),
        fetcher=MediaFetcher(),
        scenes=SceneBuilder(),
        renderer=VideoRenderer(),
    )
