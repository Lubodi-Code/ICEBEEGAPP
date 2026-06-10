"""Arranque de la app FastAPI: monta routers, CORS, estáticos y manejo de errores."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from iceberg_accesodatos import create_db_and_tables
from iceberg_api.routers import (
    entry_router,
    iceberg_router,
    level_router,
    media_router,
    public_router,
    video_router,
)
from iceberg_negocio import NotFoundError, ValidationError, VideoUnavailableError

MEDIA_LOCAL_DIR = Path("media_local")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev: crea el directorio de media local y las tablas al arrancar.
    MEDIA_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
    yield


app = FastAPI(title="Iceberg Web API", version="0.1.0", lifespan=lifespan)

# CORS abierto (solo dev).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.exception_handler(NotFoundError)
async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(VideoUnavailableError)
async def _video_unavailable_handler(request: Request, exc: VideoUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(iceberg_router.router)
app.include_router(level_router.router)
app.include_router(entry_router.router)
app.include_router(media_router.router)
app.include_router(video_router.router)
app.include_router(public_router.router)

# Dev: sirve la media guardada por el fallback local como estáticos.
app.mount(
    "/media_local",
    StaticFiles(directory=str(MEDIA_LOCAL_DIR), check_dir=False),
    name="media_local",
)
