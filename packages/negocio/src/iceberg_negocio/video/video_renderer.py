"""VideoRenderer — agrega intro/outro, concatena, sincroniza audio y exporta el .mp4."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_negocio.video.scene_builder import frame_size, make_background, text_panel

INTRO_SECONDS = 2.2
OUTRO_SECONDS = 2.0


class VideoRenderer:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def render(
        self,
        scenes: list[Any],
        *,
        audio: str | None = None,
        title: str = "",
        workdir: str | None = None,
    ) -> str:
        """Concatena intro + escenas + outro y exporta un .mp4 H.264; devuelve su ruta."""
        import numpy as np
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

        size = frame_size(self._settings)
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_video_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "iceberg.mp4"

        intro = self._card(size, "ICEBERG", title, INTRO_SECONDS, ImageClip, np)
        outro_text = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
        outro = self._card(size, "Crea el tuyo", outro_text, OUTRO_SECONDS, ImageClip, np)

        body = concatenate_videoclips(scenes) if scenes else None
        if body is not None and audio:
            body = body.with_audio(AudioFileClip(audio))

        parts = [intro] + ([body] if body is not None else []) + [outro]
        final = concatenate_videoclips(parts)
        final.write_videofile(
            str(out_path),
            fps=self._settings.video_fps,
            codec="libx264",
            audio_codec="aac",
            preset="veryfast",
            logger=None,
        )
        final.close()
        return str(out_path)

    def _card(self, size, headline: str, subtitle: str, duration: float, image_clip, np):
        """Tarjeta de intro/outro: fondo degradado + textos centrados."""
        w, h = size
        bg = make_background(size)
        head = text_panel(headline, w, max(int(h * 0.05), 36))
        canvas = bg.convert("RGBA")
        y = h // 2 - head.height
        canvas.alpha_composite(head, (0, y))
        if subtitle:
            sub = text_panel(subtitle, w, max(int(h * 0.03), 24))
            canvas.alpha_composite(sub, (0, y + head.height + int(h * 0.02)))
        return image_clip(np.array(canvas.convert("RGB"))).with_duration(duration)
