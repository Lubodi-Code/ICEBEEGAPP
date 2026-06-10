"""NarrationBuilder — arma el guion de texto a narrar."""

from __future__ import annotations

from iceberg_dto import VideoRequest


class NarrationBuilder:
    def build(self, req: VideoRequest) -> str:
        """Genera el guion: "{titulo}. Nivel {n}: {nombre}. {entrada}. {desc}."."""
        partes: list[str] = [req.iceberg_title.strip()]

        nivel = f"Nivel {req.level_number}"
        if req.level_name and req.level_name.strip():
            nivel += f": {req.level_name.strip()}"
        partes.append(nivel)

        partes.append(req.entry_title.strip())
        if req.description.strip():
            partes.append(req.description.strip())

        frases = [p.rstrip(".").strip() for p in partes if p.strip()]
        return ". ".join(frases) + "."
