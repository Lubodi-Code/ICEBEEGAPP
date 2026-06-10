"""VideoRenderer — agrega intro/outro, concatena, sincroniza audio y exporta el .mp4."""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path
from typing import Any

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_negocio.video.scene_builder import frame_size, make_background, text_panel

INTRO_SECONDS = 2.2
OUTRO_SECONDS = 2.0
SAMPLE_RATE = 22050


class VideoRenderer:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _make_silence_audio(self, duration: float, out_path: Path) -> None:
        """Crea un archivo WAV de silencio con la duración especificada."""
        n_frames = int(SAMPLE_RATE * duration)
        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(b"\x00\x00" * n_frames)

    def _build_full_audio(self, body_audio: str, out_path: Path) -> str:
        """Concatena silencio + audio + silencio usando moviepy."""
        from moviepy import AudioFileClip, concatenate_audioclips

        intro_silence = out_path.parent / "silence_intro.wav"
        outro_silence = out_path.parent / "silence_outro.wav"

        self._make_silence_audio(INTRO_SECONDS, intro_silence)
        self._make_silence_audio(OUTRO_SECONDS, outro_silence)

        # Usa moviepy para concatenar (maneja MP3 y WAV automáticamente).
        with AudioFileClip(str(intro_silence)) as intro_aud:
            with AudioFileClip(body_audio) as body_aud:
                with AudioFileClip(str(outro_silence)) as outro_aud:
                    full = concatenate_audioclips([intro_aud, body_aud, outro_aud])
                    full.write_audiofile(str(out_path), verbose=False, logger=None)

        return str(out_path)

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
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, vfx

        size = frame_size(self._settings)
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_video_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "iceberg.mp4"

        intro = self._card(size, "ICEBERG", title, INTRO_SECONDS, ImageClip, np).with_effects(
            [vfx.FadeIn(0.5), vfx.FadeOut(0.4)]
        )
        outro_text = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
        outro = self._card(
            size, "Crea el tuyo", outro_text, OUTRO_SECONDS, ImageClip, np
        ).with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.5)])

        body = concatenate_videoclips(scenes) if scenes else None

        parts = [intro] + ([body] if body is not None else []) + [outro]
        final = concatenate_videoclips(parts)

        # Si hay audio, concatena silencio + audio + silencio para cubrir intro/body/outro.
        if audio:
            full_audio = out_dir / "full_audio.wav"
            full_audio_path = self._build_full_audio(audio, full_audio)
            final = final.with_audio(AudioFileClip(full_audio_path))

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
