"""VideoRenderer — agrega intro/outro, concatena y exporta el .mp4 (STUB)."""

from __future__ import annotations

from typing import Any


class VideoRenderer:
    def render(self, scenes: list[Any]) -> str:
        """Concatena las escenas con moviepy/FFmpeg y exporta un .mp4 en /tmp.

        TODO: intro/outro, música de fondo opcional, export H.264 (9:16 o 16:9).
        """
        raise NotImplementedError("VideoRenderer.render aún no implementado")
