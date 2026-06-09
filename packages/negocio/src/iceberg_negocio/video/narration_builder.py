"""NarrationBuilder — arma el guion de texto a narrar (STUB)."""

from __future__ import annotations

from iceberg_dto import VideoRequest


class NarrationBuilder:
    def build(self, req: VideoRequest) -> str:
        """Genera el guion:
        "{titulo}. Nivel {n} {nombre}. {entrada}. {desc}".

        TODO: implementar el armado del guion a partir del VideoRequest.
        """
        raise NotImplementedError("NarrationBuilder.build aún no implementado")
