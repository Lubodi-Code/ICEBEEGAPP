"""VideoService — orquesta el pipeline de generación de video (efímero)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

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
        """Genera el .mp4 y devuelve su ruta temporal.

        Flujo: narración -> TTS -> fetch media -> escenas -> render.
        Los archivos intermedios se borran; el .mp4 queda para que la capa API
        lo sirva y lo elimine al terminar la respuesta.
        """
        workdir = Path(tempfile.mkdtemp(prefix="iceberg_video_"))
        try:
            # Cuerpo: la voz narra la entrada y su descripción.
            body_text = self.narration.build(req)
            body_audio = self.tts.synth(body_text, workdir=str(workdir / "body"))
            # Intro: la voz presenta el iceberg y el nivel durante el zoom.
            intro_text = self.narration.build_intro(req)
            intro_audio = self.tts.synth(intro_text, workdir=str(workdir / "intro"))
            assets = self.fetcher.fetch(req.media, workdir=str(workdir))

            level_label = f"Nivel {req.level_number}"
            if req.level_name:
                level_label += f" · {req.level_name}"
            # Subtítulos: solo la descripción (el título va en el header de la
            # escena y el nivel en la intro; así no se repite información).
            scenes = self.scenes.build_scenes(
                assets,
                req.description,
                body_audio,
                title=req.entry_title,
            )
            music = (
                self.fetcher.fetch_audio(req.music_url, workdir=str(workdir))
                if req.music_url
                else None
            )
            mp4 = self.renderer.render(
                scenes,
                audio=body_audio,
                intro_audio=intro_audio,
                title=req.iceberg_title,
                entry_title=req.entry_title,
                level_label=level_label,
                levels=[(lv.numero, lv.nombre) for lv in req.levels],
                level_number=req.level_number,
                slug=req.slug,
                entry_id=req.entry_id,
                music=music,
                show_url=req.show_url,
                workdir=str(workdir),
            )

            # Mueve el resultado fuera del workdir para poder limpiarlo entero.
            final = Path(tempfile.mkdtemp(prefix="iceberg_out_")) / "iceberg.mp4"
            shutil.move(mp4, final)
            return str(final)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
