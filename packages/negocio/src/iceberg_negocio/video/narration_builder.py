"""NarrationBuilder — arma el guion de texto a narrar."""

from __future__ import annotations

from iceberg_dto import VideoRequest


class NarrationBuilder:
    def build(self, req: VideoRequest) -> str:
        """Genera el guion: "{entrada}. {desc}."

        El nombre del iceberg y el nivel ya se muestran en la intro visual
        (mapa de niveles con zoom), así que no se repiten en la voz ni en
        los subtítulos.
        """
        partes: list[str] = [req.entry_title.strip()]
        if req.description.strip():
            partes.append(req.description.strip())

        frases = [p.rstrip(".").strip() for p in partes if p.strip()]
        return ". ".join(frases) + "."
