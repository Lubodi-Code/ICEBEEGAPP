"""VideoService — orquesta el pipeline de generación de video (STUB)."""

from __future__ import annotations

from iceberg_dto import VideoRequest
from iceberg_negocio.video.media_fetcher import MediaFetcher
from iceberg_negocio.video.narration_builder import NarrationBuilder
from iceberg_negocio.video.scene_builder import SceneBuilder
from iceberg_negocio.video.tts_engine import TTSEngine
from iceberg_negocio.video.video_renderer import VideoRenderer


class VideoService:
    def __init__(
        self,
        narration: NarrationBuilder,
        tts: TTSEngine,
        fetcher: MediaFetcher,
        scenes: SceneBuilder,
        renderer: VideoRenderer,
    ) -> None:
        self.narration = narration
        self.tts = tts
        self.fetcher = fetcher
        self.scenes = scenes
        self.renderer = renderer

    def generate(self, req: VideoRequest) -> str:
        """Genera el .mp4 y devuelve su ruta en /tmp.

        Flujo previsto: narración -> TTS -> fetch media -> escenas -> render.
        TODO: implementar la orquestación completa del pipeline.
        """
        raise NotImplementedError("VideoService.generate aún no implementado")
