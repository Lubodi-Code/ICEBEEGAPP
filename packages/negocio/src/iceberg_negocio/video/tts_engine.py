"""TTSEngine — convierte el guion en audio (STUB).

Piper para voz neuronal o eSpeak-NG para el sonido robótico clásico tipo loquendo.
"""

from __future__ import annotations


class TTSEngine:
    def synth(self, text: str) -> str:
        """Sintetiza ``text`` a un WAV y devuelve su ruta en /tmp.

        TODO: integrar Piper / eSpeak-NG (voz y velocidad configurables).
        """
        raise NotImplementedError("TTSEngine.synth aún no implementado")
