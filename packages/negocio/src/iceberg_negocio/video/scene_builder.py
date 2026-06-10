"""SceneBuilder — compone las escenas con la multimedia de la entrada.

A las imágenes les da un zoom suave (Ken Burns) y a los clips de video los
recorta a su porción de la narración; sobre cada escena superpone el título,
el indicador de nivel y los subtítulos. Usa Pillow + moviepy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from iceberg_accesodatos.config import Settings, get_settings

IMAGE_EXTS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}
KEN_BURNS_ZOOM = 0.08  # zoom total a lo largo de la escena (8%)

# Paleta "iceberg": degradado azul profundo.
GRADIENT_TOP = (12, 36, 64)
GRADIENT_BOTTOM = (2, 8, 20)


def frame_size(settings: Settings) -> tuple[int, int]:
    """(ancho, alto) según VIDEO_ASPECT."""
    return (1280, 720) if settings.video_aspect == "16:9" else (720, 1280)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "arial.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def make_background(size: tuple[int, int]) -> Image.Image:
    """Degradado vertical azul profundo (tema iceberg)."""
    w, h = size
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(
            int(GRADIENT_TOP[c] + (GRADIENT_BOTTOM[c] - GRADIENT_TOP[c]) * t) for c in range(3)
        )
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=color)
    return img


def text_panel(
    text: str,
    width: int,
    font_size: int,
    *,
    align: str = "center",
    pad: int = 16,
) -> Image.Image:
    """Panel RGBA con el texto envuelto sobre una banda semitransparente."""
    font = _font(font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (width, 10)))
    lines = _wrap(probe, text, font, width - 2 * pad)
    line_h = int(font_size * 1.3)
    height = 2 * pad + line_h * max(len(lines), 1)

    panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    band = Image.new("RGBA", (width, height), (0, 0, 0, 130))
    band = band.filter(ImageFilter.GaussianBlur(0))
    panel.alpha_composite(band)
    draw = ImageDraw.Draw(panel)
    y = pad
    for line in lines:
        if align == "center":
            x = (width - draw.textlength(line, font=font)) // 2
        else:
            x = pad
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 200),
        )
        y += line_h
    return panel


def cover_fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Escala y recorta al centro para cubrir ``size`` por completo."""
    w, h = size
    scale = max(w / img.width, h / img.height)
    resized = img.resize((round(img.width * scale), round(img.height * scale)))
    left = (resized.width - w) // 2
    top = (resized.height - h) // 2
    return resized.crop((left, top, left + w, top + h))


def _split_chunks(text: str, n: int) -> list[str]:
    """Reparte las palabras del guion en ``n`` bloques de subtítulo."""
    words = text.split()
    if not words:
        return [""] * n
    per = max(len(words) // n, 1)
    chunks = [" ".join(words[i * per : (i + 1) * per]) for i in range(n - 1)]
    chunks.append(" ".join(words[(n - 1) * per :]))
    return chunks


class SceneBuilder:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def build_scenes(
        self,
        assets: list[str],
        text: str,
        audio: str,
        *,
        title: str = "",
        level_label: str = "",
    ) -> list[Any]:
        """Devuelve una lista de clips moviepy cuya duración total = duración del audio."""
        import numpy as np
        from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip, vfx

        size = frame_size(self._settings)
        w, h = size

        with AudioFileClip(audio) as audio_clip:
            total = float(audio_clip.duration)

        usable = assets or [None]  # sin multimedia: una escena con fondo degradado
        per_scene = total / len(usable)
        chunks = _split_chunks(text, len(usable))

        # Overlays constantes (título arriba, badge de nivel debajo).
        header = text_panel(title, w, max(int(h * 0.030), 26)) if title else None
        badge = text_panel(level_label, w, max(int(h * 0.024), 20)) if level_label else None

        scenes: list[Any] = []
        for i, asset in enumerate(usable):
            if asset is None or Path(asset).suffix.lower() in IMAGE_EXTS:
                base = self._image_scene(asset, size, per_scene, ImageClip, np)
            else:
                base = self._video_scene(asset, size, per_scene, VideoFileClip, ImageClip, np)

            layers = [base]
            if header is not None:
                layers.append(
                    ImageClip(np.array(header))
                    .with_duration(per_scene)
                    .with_position(("center", 0))
                )
            if badge is not None:
                layers.append(
                    ImageClip(np.array(badge))
                    .with_duration(per_scene)
                    .with_position(("center", header.height if header is not None else 0))
                )
            if chunks[i]:
                sub = text_panel(chunks[i], w, max(int(h * 0.026), 22))
                layers.append(
                    ImageClip(np.array(sub))
                    .with_duration(per_scene)
                    .with_position(("center", h - sub.height - int(h * 0.04)))
                )
            scene = CompositeVideoClip(layers, size=size).with_duration(per_scene)
            # Transición suave entre escenas (~0.4s, acotada en escenas muy cortas).
            fade = min(0.4, per_scene / 4)
            scenes.append(scene.with_effects([vfx.FadeIn(fade), vfx.FadeOut(fade)]))
        return scenes

    def _image_scene(
        self, asset: str | None, size: tuple[int, int], duration: float, image_clip, np
    ):
        """Imagen estática con zoom Ken Burns lento."""
        w, h = size
        if asset is None:
            frame = make_background(size)
        else:
            with Image.open(asset) as img:
                frame = cover_fit(img.convert("RGB"), size)

        # Margen extra para que el zoom nunca deje bordes vacíos.
        oversize = (int(w * (1 + KEN_BURNS_ZOOM)), int(h * (1 + KEN_BURNS_ZOOM)))
        big = cover_fit(frame, oversize)
        clip = image_clip(np.array(big)).with_duration(duration)
        zoom = lambda t: 1.0 + KEN_BURNS_ZOOM * (t / max(duration, 0.01))  # noqa: E731
        return clip.resized(zoom).with_position("center")

    def _video_scene(
        self, asset: str, size: tuple[int, int], duration: float, video_file_clip, image_clip, np
    ):
        """Clip de video recortado (cover) y ajustado a la duración de la escena."""
        w, h = size
        clip = video_file_clip(asset).without_audio()
        scale = max(w / clip.w, h / clip.h)
        clip = clip.resized(scale).cropped(
            x_center=clip.w * scale / 2, y_center=clip.h * scale / 2, width=w, height=h
        )
        if clip.duration >= duration:
            return clip.subclipped(0, duration)
        # Más corto que la escena: congela el último frame para completar.
        freeze = image_clip(clip.get_frame(max(clip.duration - 0.05, 0))).with_duration(
            duration - clip.duration
        )
        from moviepy import concatenate_videoclips

        return concatenate_videoclips([clip, freeze])
