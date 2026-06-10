"""TTSEngine — convierte el guion en audio WAV.

Motores soportados (variable ``TTS_ENGINE``):

- ``espeak``: eSpeak-NG vía subprocess (el sonido robótico clásico tipo loquendo).
- ``piper``: voz neuronal; requiere el binario ``piper`` y un modelo ``.onnx``
  (``PIPER_VOICE``).
- ``silent``: genera un WAV de silencio proporcional al texto. Útil para dev/tests
  en máquinas sin TTS instalado.
"""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from iceberg_accesodatos.config import Settings, get_settings
from iceberg_negocio.errors import VideoUnavailableError

SAMPLE_RATE = 22050


class TTSEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def synth(self, text: str, workdir: str | None = None) -> str:
        """Sintetiza ``text`` a un WAV y devuelve su ruta local."""
        out_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="iceberg_tts_"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "narracion.wav"

        engine = self._settings.tts_engine.lower().strip()
        if engine == "espeak":
            self._synth_espeak(text, out_path)
        elif engine == "piper":
            self._synth_piper(text, out_path)
        elif engine == "silent":
            self._synth_silent(text, out_path)
        else:
            raise VideoUnavailableError(f"Motor TTS desconocido: {engine!r}")
        return str(out_path)

    def _synth_espeak(self, text: str, out_path: Path) -> None:
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        if binary is None:
            raise VideoUnavailableError(
                "eSpeak-NG no está instalado; instala 'espeak-ng' o usa TTS_ENGINE=silent"
            )
        result = subprocess.run(
            [
                binary,
                "-v",
                self._settings.espeak_voice,
                "-s",
                str(self._settings.espeak_speed),
                "-w",
                str(out_path),
                text,
            ],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0 or not out_path.exists():
            raise VideoUnavailableError(
                f"eSpeak-NG falló: {result.stderr.decode(errors='replace')[:200]}"
            )

    def _synth_piper(self, text: str, out_path: Path) -> None:
        binary = shutil.which("piper")
        if binary is None:
            raise VideoUnavailableError("Piper no está instalado; instala 'piper-tts'")
        if not self._settings.piper_voice:
            raise VideoUnavailableError("Falta PIPER_VOICE (ruta al modelo .onnx de Piper)")
        result = subprocess.run(
            [binary, "--model", self._settings.piper_voice, "--output_file", str(out_path)],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0 or not out_path.exists():
            raise VideoUnavailableError(
                f"Piper falló: {result.stderr.decode(errors='replace')[:200]}"
            )

    def _synth_silent(self, text: str, out_path: Path) -> None:
        """WAV casi-silencioso cuya duración aproxima una narración (~2.6 palabras/seg)."""
        words = max(len(text.split()), 1)
        duration = max(2.0, words / 2.6)
        n_frames = int(SAMPLE_RATE * duration)
        with wave.open(str(out_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            # Tono apenas audible (evita streams 100% nulos que algunos players recortan).
            frames = bytearray()
            for i in range(n_frames):
                sample = int(80 * math.sin(2 * math.pi * 220 * i / SAMPLE_RATE))
                frames += struct.pack("<h", sample)
            wav.writeframes(bytes(frames))
