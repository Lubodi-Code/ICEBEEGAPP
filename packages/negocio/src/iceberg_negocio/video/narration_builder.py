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

    def build_intro(self, req: VideoRequest) -> str:
        """Locución de la intro: nombre del iceberg y nivel.

        Se reproduce sobre la vista lejana mientras la cámara hace zoom al
        nivel elegido, así la voz presenta el iceberg y el nivel sin repetirlos
        luego en el cuerpo del video.
        """
        partes: list[str] = []
        if req.iceberg_title.strip():
            partes.append(req.iceberg_title.strip())

        nivel = f"Nivel {req.level_number}"
        if req.level_name and req.level_name.strip():
            nivel += f": {req.level_name.strip()}"
        partes.append(nivel)

        frases = [p.rstrip(".").strip() for p in partes if p.strip()]
        return ". ".join(frases) + "."
