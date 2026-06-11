# Imagen del backend (API + futuro pipeline de video). Compatible con Hugging Face Spaces.
FROM python:3.12-slim

# FFmpeg + eSpeak-NG: necesarios para el pipeline de video (TTS + render).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Instalador/gestor uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY . .

# Instala el workspace completo (root virtual -> api -> negocio -> ... -> entities).
# --no-dev: omite pytest/ruff/import-linter en la imagen de producción.
RUN uv sync --no-dev

# Chromium para Playwright: la intro del video captura una screenshot real del
# editor (modo mapa). Sin el navegador, el render cae al mapa dibujado con Pillow.
RUN uv run playwright install --with-deps chromium

# Frontend público (SPA en Vercel) al que Playwright apunta para la captura.
# Puede sobreescribirse con una variable del Space.
ENV FRONTEND_BASE_URL=https://icebeegapp.vercel.app

# HF Spaces escucha en 7860.
EXPOSE 7860
CMD ["uv", "run", "uvicorn", "iceberg_api.main:app", "--host", "0.0.0.0", "--port", "7860"]
