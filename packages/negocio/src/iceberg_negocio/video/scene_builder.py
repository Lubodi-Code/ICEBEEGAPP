"""SceneBuilder — compone las escenas con la multimedia de la entrada (STUB).

A las imágenes les da un zoom suave (Ken Burns) y a los clips los recorta; sobre
cada escena superpone el título, el indicador de nivel y los subtítulos.
Usa Pillow y moviepy.
"""

from __future__ import annotations

from typing import Any


class SceneBuilder:
    def build_scenes(self, assets: list[str], text: str, audio: str) -> list[Any]:
        """Devuelve una lista de clips (moviepy) sincronizados con el audio.

        TODO: implementar Ken Burns para imágenes, recorte de video y overlays
        (título + nivel + subtítulos) con Pillow + moviepy.
        """
        raise NotImplementedError("SceneBuilder.build_scenes aún no implementado")
