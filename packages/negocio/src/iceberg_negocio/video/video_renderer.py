"""VideoRenderer — agrega intro/outro, concatena, sincroniza audio y exporta el .mp4."""

from __future__ import annotations

import logging
import tempfile
import wave
from pathlib import Path
from typing import Any

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_negocio.video.scene_builder import (
    _font,
    _wrap,
    frame_size,
    make_background,
)

INTRO_SECONDS = 3.2
OUTRO_SECONDS = 2.6
MAP_SUPERSAMPLE = 2.4  # el mapa de niveles se dibuja a esta escala para el zoom
MAP_HOLD = 0.8  # segundos de vista lejana antes de empezar el zoom
MAP_ZOOM_TIME = 1.6  # duración del acercamiento al nivel elegido
SAMPLE_RATE = 22050
INTRO_ZOOM = 0.10  # zoom lento del fondo de la intro (10%)
MUSIC_VOLUME = 0.20  # volumen de la música bajo la narración
MUSIC_FADEOUT = 1.5  # segundos de fundido de salida de la música


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

    def _build_full_audio(
        self,
        body_audio: str,
        out_path: Path,
        *,
        intro_audio: str | None = None,
        intro_dur: float = INTRO_SECONDS,
    ) -> str:
        """Concatena intro + cuerpo + silencio final usando moviepy.

        El tramo de intro dura ``intro_dur`` exactamente (igual que el clip de
        intro del video): si hay ``intro_audio`` (voz de presentación) se usa esa
        voz y se rellena con silencio hasta completar ``intro_dur``; si no, es
        todo silencio.
        """
        from moviepy import AudioFileClip, concatenate_audioclips

        out_dir = out_path.parent
        outro_silence = out_dir / "silence_outro.wav"
        self._make_silence_audio(OUTRO_SECONDS, outro_silence)

        opened: list[Any] = []
        parts: list[Any] = []

        if intro_audio:
            intro_aud = AudioFileClip(intro_audio)
            opened.append(intro_aud)
            parts.append(intro_aud)
            pad = intro_dur - float(intro_aud.duration)
            if pad > 0.02:
                pad_path = out_dir / "silence_intro_pad.wav"
                self._make_silence_audio(pad, pad_path)
                pad_aud = AudioFileClip(str(pad_path))
                opened.append(pad_aud)
                parts.append(pad_aud)
        else:
            intro_silence = out_dir / "silence_intro.wav"
            self._make_silence_audio(intro_dur, intro_silence)
            intro_aud = AudioFileClip(str(intro_silence))
            opened.append(intro_aud)
            parts.append(intro_aud)

        body_aud = AudioFileClip(body_audio)
        opened.append(body_aud)
        parts.append(body_aud)

        outro_aud = AudioFileClip(str(outro_silence))
        opened.append(outro_aud)
        parts.append(outro_aud)

        try:
            full = concatenate_audioclips(parts)
            full.write_audiofile(str(out_path), logger=None)
            full.close()
        finally:
            for clip in opened:
                clip.close()

        return str(out_path)

    def render(
        self,
        scenes: list[Any],
        *,
        audio: str | None = None,
        intro_audio: str | None = None,
        title: str = "",
        entry_title: str = "",
        level_label: str = "",
        levels: list[tuple[int, str | None]] | None = None,
        level_number: int = 0,
        slug: str | None = None,
        entry_id: str | None = None,
        music: str | None = None,
        show_url: bool = False,
        workdir: str | None = None,
    ) -> str:
        """Concatena intro cinematográfica + escenas + outro y exporta un .mp4 H.264."""
        import numpy as np
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

        size = frame_size(self._settings)
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_video_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "iceberg.mp4"

        # La intro dura lo que la locución de presentación (voz del iceberg/nivel)
        # más una pequeña cola; nunca menos que el mínimo cinematográfico. Esta
        # misma duración se usa para el clip de intro y para el tramo de audio,
        # de modo que el cuerpo siga perfectamente alineado con sus escenas.
        intro_dur = INTRO_SECONDS
        if intro_audio:
            with AudioFileClip(intro_audio) as ia:
                intro_dur = max(INTRO_SECONDS, float(ia.duration) + 0.5)

        # Intro: mapa de niveles con zoom al elegido; sin niveles, tarjeta clásica.
        if levels:
            intro = self._levels_intro(
                size,
                title,
                entry_title,
                levels,
                level_number,
                ImageClip,
                np,
                dur=intro_dur,
                slug=slug,
                entry_id=entry_id,
                out_dir=out_dir,
            )
        else:
            intro = self._intro(
                size, title, entry_title, level_label, ImageClip, np, dur=intro_dur
            )

        # Outro: nunca muestra URLs de localhost; opcionalmente ninguna.
        outro_text = ""
        if show_url:
            url = self._settings.public_base_url.removeprefix("https://").removeprefix("http://")
            if not url.startswith(("localhost", "127.0.0.1", "0.0.0.0")):
                outro_text = url
        outro = self._outro(size, outro_text, ImageClip, np)

        body = concatenate_videoclips(scenes) if scenes else None

        parts = [intro] + ([body] if body is not None else []) + [outro]
        final = concatenate_videoclips(parts)
        # El video es opaco: descartar la máscara evita un bug de moviepy al
        # componer máscaras de clips que sobresalen del lienzo (zoom del mapa).
        final.mask = None

        # Audio: narración SIEMPRE; la música solo se mezcla si se puede decodificar.
        audio_path = self._compose_audio(
            audio, music, final.duration, out_dir, intro_audio=intro_audio, intro_dur=intro_dur
        )
        if audio_path is not None:
            final = final.with_audio(AudioFileClip(audio_path))

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

    # ------------------------------------------------------------------ intro

    def _levels_intro(
        self,
        size,
        iceberg_title: str,
        entry_title: str,
        levels: list[tuple[int, str | None]],
        target_number: int,
        image_clip,
        np,
        *,
        dur: float = INTRO_SECONDS,
        slug: str | None = None,
        entry_id: str | None = None,
        out_dir: Path | None = None,
    ):
        """Vista lejana de todos los niveles y zoom suave hacia el nivel elegido.

        Si es posible, usa una screenshot real del editor (modo mapa) vía
        Playwright; si no, cae al mapa dibujado con Pillow. En ambos casos la
        imagen tiene la proporción del cuadro, así que ``res`` se deduce de ella.
        """
        from moviepy import CompositeVideoClip, vfx

        w, h = size

        map_img, (xc, yc), band_h_hi = self._build_map_image(
            size, iceberg_title, entry_title, levels, target_number, slug, entry_id, out_dir
        )
        # La imagen es proporcional al cuadro; res = cuánto la sobremuestrea.
        res = map_img.width / float(w)

        # Zoom final: que la banda elegida ocupe ~media pantalla (sin pasar la
        # resolución a la que se dibujó/capturó el mapa).
        band_h_screen = band_h_hi / res
        s_final = min(2.1, max(1.5, (h * 0.42) / max(band_h_screen, 1.0)))

        # El zoom se acompasa a la intro (que dura lo que la voz de presentación):
        # breve vista lejana, acercamiento mientras se nombra el nivel, y cola.
        hold = min(MAP_HOLD, dur * 0.32)
        zoom_time = min(MAP_ZOOM_TIME, max(dur - hold - 0.4, 0.6))

        def prog(t: float) -> float:
            """Progreso del zoom con suavizado (espera, acelera, frena)."""
            u = (t - hold) / zoom_time
            u = min(max(u, 0.0), 1.0)
            return u * u * (3.0 - 2.0 * u)

        big_w, big_h = map_img.width, map_img.height

        def disp(t: float) -> float:
            """Escala de presentación del mapa hi-res en pantalla."""
            return (1.0 + (s_final - 1.0) * prog(t)) / res

        def pos(t: float):
            d = disp(t)
            u = prog(t)
            # Mezcla entre "mapa completo centrado" y "nivel elegido al centro".
            centered = ((w - d * big_w) / 2.0, (h - d * big_h) / 2.0)
            target = (w / 2.0 - d * xc, h * 0.5 - d * yc)
            return (
                (1.0 - u) * centered[0] + u * target[0],
                (1.0 - u) * centered[1] + u * target[1],
            )

        clip = (
            image_clip(np.array(map_img))
            .with_duration(dur)
            .resized(disp)
            .with_position(pos)
        )
        intro = CompositeVideoClip([clip], size=size).with_duration(dur)
        return intro.with_effects([vfx.FadeIn(0.45), vfx.FadeOut(0.5)])

    def _build_map_image(
        self,
        size,
        iceberg_title: str,
        entry_title: str,
        levels: list[tuple[int, str | None]],
        target_number: int,
        slug: str | None,
        entry_id: str | None,
        out_dir: Path | None,
    ):
        """Imagen del mapa hi-res: screenshot real del editor o, si falla, dibujada.

        Devuelve ``(imagen_pillow, (centro_x, centro_y), alto_banda)`` en píxeles
        de la imagen, con la misma semántica en ambos caminos.
        """
        from PIL import Image

        w, h = size

        # Camino preferido: foto real de la SPA (solo si tenemos a dónde apuntar).
        if slug and entry_id and out_dir is not None:
            try:
                from iceberg_negocio.video.map_screenshotter import capture_map

                png, xc, yc, band_h = capture_map(
                    slug,
                    entry_id,
                    self._settings.frontend_base_url,
                    out_dir / "map_shot.png",
                    width=w,
                    height=h,
                    scale=int(round(MAP_SUPERSAMPLE)) or 2,
                )
                img = Image.open(png).convert("RGB")
                return img, (xc, yc), band_h
            except Exception:
                # Playwright ausente, frontend caído o timeout: usamos el dibujo.
                logging.getLogger(__name__).warning(
                    "Screenshot del mapa falló (frontend=%s); usando mapa dibujado",
                    self._settings.frontend_base_url,
                    exc_info=True,
                )

        return self._draw_levels_map(
            size, MAP_SUPERSAMPLE, iceberg_title, entry_title, levels, target_number
        )

    def _draw_levels_map(
        self,
        size,
        scale: float,
        iceberg_title: str,
        entry_title: str,
        levels: list[tuple[int, str | None]],
        target_number: int,
    ):
        """Dibuja el mapa del iceberg (todas las capas) a alta resolución.

        Devuelve ``(imagen, centro_del_nivel_elegido, alto_de_banda)`` en píxeles
        de la imagen hi-res.
        """
        from PIL import Image, ImageDraw

        w, h = size
        big_w, big_h = int(w * scale), int(h * scale)
        base = make_background((big_w, big_h)).convert("RGBA")
        overlay = Image.new("RGBA", (big_w, big_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        def mix(a, b, t):
            return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))

        # Título del iceberg arriba.
        title_font = _font(max(int(big_h * 0.024), 22))
        title = (iceberg_title or "ICEBERG").upper()
        tw = draw.textlength(title, font=title_font)
        draw.text(
            ((big_w - tw) / 2, big_h * 0.035),
            title,
            font=title_font,
            fill=(160, 215, 240, 255),
            stroke_width=max(int(scale), 2),
            stroke_fill=(0, 0, 0, 160),
        )
        # Línea de flotación bajo el título.
        wl_y = big_h * 0.085
        draw.line(
            [(big_w * 0.10, wl_y), (big_w * 0.90, wl_y)],
            fill=(120, 200, 220, 110),
            width=max(int(scale), 2),
        )

        # Bandas de niveles: descienden oscureciéndose como el océano.
        n = len(levels)
        top, bottom = big_h * 0.115, big_h * 0.965
        gap = big_h * 0.014
        band_h = (bottom - top - gap * (n - 1)) / n
        x0, x1 = big_w * 0.07, big_w * 0.93
        radius = big_h * 0.014
        label_font = _font(max(int(band_h * 0.16), 18))
        chip_font = _font(max(int(big_h * 0.022), 20))

        target_center = (big_w / 2.0, big_h / 2.0)
        for i, (numero, nombre) in enumerate(levels):
            t = i / max(n - 1, 1)
            y0 = top + i * (band_h + gap)
            y1 = y0 + band_h
            is_target = numero == target_number

            fill = mix((36, 86, 120), (8, 18, 34), t)
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=radius,
                fill=(*fill, 215),
                outline=(216, 177, 90, 255) if is_target else (255, 255, 255, 55),
                width=max(int(scale * (3 if is_target else 1.2)), 2),
            )

            label = f"NIVEL {numero}"
            if nombre:
                label += f" · {nombre}"
            # Centrada: sobrevive al encuadre cuando la cámara hace zoom a la banda.
            label_w = draw.textlength(label, font=label_font)
            draw.text(
                ((big_w - label_w) / 2, y0 + band_h * 0.10),
                label,
                font=label_font,
                fill=(230, 240, 250, 235) if is_target else (175, 195, 215, 180),
            )

            if is_target:
                target_center = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
                # Ficha de la entrada elegida, centrada en la banda.
                text_w = draw.textlength(entry_title, font=chip_font)
                pad_x, pad_y = big_w * 0.025, big_h * 0.012
                cw = min(text_w + 2 * pad_x, (x1 - x0) * 0.84)
                ch = chip_font.size + 2 * pad_y
                cx0 = (big_w - cw) / 2
                cy0 = (y0 + y1) / 2 - ch / 2 + band_h * 0.08
                draw.rounded_rectangle(
                    [cx0, cy0, cx0 + cw, cy0 + ch],
                    radius=radius * 0.6,
                    fill=(8, 14, 24, 240),
                    outline=(216, 177, 90, 230),
                    width=max(int(scale * 1.5), 2),
                )
                draw.text(
                    (cx0 + (cw - min(text_w, cw - 2 * pad_x)) / 2, cy0 + pad_y),
                    entry_title,
                    font=chip_font,
                    fill=(255, 255, 255, 255),
                )
                # "Chincheta" roja sobre la ficha (como en el editor).
                pin_r = big_h * 0.005
                pcx, pcy = (cx0 + cw / 2, cy0)
                draw.ellipse(
                    [pcx - pin_r, pcy - pin_r, pcx + pin_r, pcy + pin_r],
                    fill=(205, 70, 70, 255),
                )

        base.alpha_composite(overlay)
        return base.convert("RGB"), target_center, band_h

    def _intro(
        self,
        size,
        iceberg_title: str,
        entry_title: str,
        level_label: str,
        image_clip,
        np,
        *,
        dur: float = INTRO_SECONDS,
    ):
        """Intro cinematográfica: fondo con foco y viñeta en zoom lento + textos escalonados."""
        from moviepy import CompositeVideoClip, vfx

        w, h = size

        # Fondo sobredimensionado para que el zoom nunca deje bordes.
        bg_img = self._intro_background((int(w * (1 + INTRO_ZOOM)), int(h * (1 + INTRO_ZOOM))), np)
        zoom = lambda t: 1.0 + INTRO_ZOOM * (t / dur)  # noqa: E731
        bg = (
            image_clip(np.array(bg_img))
            .with_duration(dur)
            .resized(zoom)
            .with_position("center")
        )

        layers: list[Any] = [bg]

        def add_text(img, y_frac: float, start: float, drift: int = 18) -> None:
            """Apila un texto que aparece en ``start`` con fundido y deriva vertical suave."""
            y0 = int(h * y_frac)
            clip = (
                image_clip(np.array(img))
                .with_start(start)
                .with_duration(dur - start)
                .with_position(
                    lambda t, y0=y0, drift=drift: (
                        "center",
                        y0 + int(drift * max(0.0, 1.0 - t / 0.7)),
                    )
                )
                .with_effects([vfx.CrossFadeIn(0.55)])
            )
            layers.append(clip)

        # Kicker arriba: nombre del iceberg en pequeño y espaciado.
        kicker = (iceberg_title or "ICEBERG").upper()
        kicker_img = self._text_image(
            kicker, w, max(int(h * 0.020), 18), (140, 220, 180, 255), np
        )
        add_text(kicker_img, 0.30, 0.25, drift=10)

        # Título de la entrada: grande, centrado.
        if entry_title:
            title_img = self._text_image(
                entry_title, w, max(int(h * 0.046), 34), (255, 255, 255, 255), np
            )
            add_text(title_img, 0.40, 0.65)

        # Línea separadora + nivel debajo.
        rule_img = self._rule_image(int(w * 0.32), 3, (216, 177, 90, 220), np)
        add_text(rule_img, 0.55, 1.0, drift=8)
        if level_label:
            level_img = self._text_image(
                level_label, w, max(int(h * 0.024), 20), (216, 177, 90, 255), np
            )
            add_text(level_img, 0.58, 1.15, drift=12)

        intro = CompositeVideoClip(layers, size=size).with_duration(dur)
        return intro.with_effects([vfx.FadeIn(0.45), vfx.FadeOut(0.5)])

    def _intro_background(self, size, np):
        """Degradado profundo + foco de luz central + viñeta (fondo de la intro)."""
        from PIL import Image

        w, h = size
        base = make_background(size).convert("RGB")
        arr = np.asarray(base).astype(np.float32)

        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2.0, h * 0.42
        dist = np.sqrt(((xx - cx) / (0.72 * w)) ** 2 + ((yy - cy) / (0.72 * h)) ** 2)

        # Foco azul-verdoso que ilumina la zona del título.
        glow = np.clip(1.0 - dist, 0.0, 1.0) ** 2
        arr += glow[..., None] * np.array([18.0, 52.0, 70.0])

        # Viñeta: oscurece bordes y esquinas.
        vignette = np.clip(dist - 0.55, 0.0, 1.0) ** 1.5
        arr *= (1.0 - 0.6 * vignette)[..., None]

        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def _text_image(self, text: str, width: int, font_size: int, color, np):
        """Texto centrado sobre fondo transparente (sin banda), con borde suave."""
        from PIL import Image, ImageDraw

        font = _font(font_size)
        probe = ImageDraw.Draw(Image.new("RGBA", (width, 10)))
        lines = _wrap(probe, text, font, int(width * 0.84))
        line_h = int(font_size * 1.3)
        img = Image.new("RGBA", (width, line_h * max(len(lines), 1) + 8), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        y = 4
        for line in lines:
            x = (width - draw.textlength(line, font=font)) // 2
            draw.text(
                (x, y),
                line,
                font=font,
                fill=color,
                stroke_width=max(font_size // 14, 2),
                stroke_fill=(0, 0, 0, 170),
            )
            y += line_h
        return img

    def _rule_image(self, width: int, height: int, color, np):
        """Línea horizontal decorativa con extremos desvanecidos."""
        from PIL import Image

        img = Image.new("RGBA", (width, height), color)
        alpha = np.asarray(img.split()[3]).astype(np.float32)
        fade = np.minimum(np.arange(width) / (width * 0.25), 1.0)
        fade = np.minimum(fade, fade[::-1])
        alpha *= fade[None, :]
        img.putalpha(Image.fromarray(alpha.astype(np.uint8)))
        return img

    # ------------------------------------------------------------------ outro

    def _outro(self, size, url_text: str, image_clip, np):
        """Outro con el mismo acabado que la intro: invitación a crear el propio iceberg."""
        from moviepy import CompositeVideoClip, vfx

        w, h = size
        dur = OUTRO_SECONDS

        bg_img = self._intro_background((int(w * (1 + INTRO_ZOOM)), int(h * (1 + INTRO_ZOOM))), np)
        # Zoom inverso al de la intro: la cámara se aleja suavemente.
        zoom = lambda t: 1.0 + INTRO_ZOOM * (1.0 - t / dur)  # noqa: E731
        bg = (
            image_clip(np.array(bg_img))
            .with_duration(dur)
            .resized(zoom)
            .with_position("center")
        )

        layers: list[Any] = [bg]

        def add_text(img, y_frac: float, start: float, drift: int = 14) -> None:
            y0 = int(h * y_frac)
            clip = (
                image_clip(np.array(img))
                .with_start(start)
                .with_duration(dur - start)
                .with_position(
                    lambda t, y0=y0, drift=drift: (
                        "center",
                        y0 + int(drift * max(0.0, 1.0 - t / 0.6)),
                    )
                )
                .with_effects([vfx.CrossFadeIn(0.45)])
            )
            layers.append(clip)

        kicker_img = self._text_image(
            "¿CONOCES MÁS SECRETOS?", w, max(int(h * 0.020), 18), (140, 220, 180, 255), np
        )
        add_text(kicker_img, 0.36, 0.15, drift=8)

        title_img = self._text_image(
            "Crea el tuyo", w, max(int(h * 0.052), 38), (255, 255, 255, 255), np
        )
        add_text(title_img, 0.44, 0.45)

        rule_img = self._rule_image(int(w * 0.28), 3, (216, 177, 90, 220), np)
        add_text(rule_img, 0.56, 0.75, drift=6)

        footer = url_text or "y comparte tus propios misterios"
        footer_img = self._text_image(
            footer, w, max(int(h * 0.024), 20), (216, 177, 90, 255), np
        )
        add_text(footer_img, 0.59, 0.9, drift=10)

        outro = CompositeVideoClip(layers, size=size).with_duration(dur)
        return outro.with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.55)])

    # ------------------------------------------------------------------ audio

    def _compose_audio(
        self,
        narration: str | None,
        music: str | None,
        duration: float,
        out_dir: Path,
        *,
        intro_audio: str | None = None,
        intro_dur: float = INTRO_SECONDS,
    ) -> str | None:
        """Devuelve la ruta de un WAV final con narración + música mezcladas.

        La narración (voz TTS) es la pista principal y SIEMPRE se conserva. La música
        se decodifica a PCM con numpy, se repite en loop hasta cubrir el video, se baja
        de volumen y se suma; si algo falla con la música, se devuelve solo la voz.
        """
        narration_path: str | None = None
        if narration:
            narration_path = self._build_full_audio(
                narration,
                out_dir / "full_audio.wav",
                intro_audio=intro_audio,
                intro_dur=intro_dur,
            )

        if not music:
            return narration_path

        try:
            return self._mix_with_music(narration_path, music, duration, out_dir)
        except Exception:
            # Música corrupta o formato no soportado: el video sale solo con la voz.
            return narration_path

    def _decode_to_pcm(self, src: str, rate: int, out_path: Path, np):
        """Decodifica cualquier audio a PCM mono float64 vía ffmpeg (el de moviepy)."""
        import subprocess

        from moviepy.config import FFMPEG_BINARY

        subprocess.run(  # noqa: S603
            [
                FFMPEG_BINARY,
                "-y",
                "-i",
                src,
                "-ac",
                "1",
                "-ar",
                str(rate),
                "-acodec",
                "pcm_s16le",
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )
        with wave.open(str(out_path), "rb") as wav:
            raw = wav.readframes(wav.getnframes())
        return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0

    def _mix_with_music(
        self, narration_path: str | None, music: str, duration: float, out_dir: Path
    ) -> str:
        """Mezcla determinista en PCM: voz a volumen pleno + música en loop atenuada."""
        import numpy as np

        rate = 44100
        n_total = max(int(duration * rate), 1)

        # Música -> mono float, en loop hasta cubrir todo el video, atenuada.
        msamples = self._decode_to_pcm(music, rate, out_dir / "music_pcm.wav", np)
        if not len(msamples):
            raise ValueError("música sin samples")
        reps = n_total // len(msamples) + 1
        mix = np.tile(msamples, reps)[:n_total] * MUSIC_VOLUME

        # Fundido de salida de la música al final del video.
        n_fade = min(int(MUSIC_FADEOUT * rate), n_total)
        if n_fade > 0:
            mix[-n_fade:] *= np.linspace(1.0, 0.0, n_fade)

        # Voz encima, a volumen pleno.
        if narration_path:
            voice = self._decode_to_pcm(narration_path, rate, out_dir / "voice_pcm.wav", np)
            n = min(len(voice), n_total)
            mix[:n] += voice[:n]

        mix = np.clip(mix, -1.0, 1.0)
        out = out_dir / "mixed_audio.wav"
        with wave.open(str(out), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes((mix * 32767).astype(np.int16).tobytes())
        return str(out)
