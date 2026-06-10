"""Configuración de tests: base de datos SQLite temporal aislada.

El entorno se fija a nivel de módulo (antes de importar la app) para que el engine
*lazy* se construya apuntando a la base de datos temporal.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# --- entorno aislado, fijado antes de importar la app -----------------------
_TMP_DIR = tempfile.mkdtemp(prefix="iceberg_test_")
_DB_PATH = Path(_TMP_DIR, "test.db").as_posix()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["PUBLIC_BASE_URL"] = "http://testserver"
# Pipeline de video reproducible sin TTS instalado y con render rápido.
os.environ["TTS_ENGINE"] = "silent"
os.environ["VIDEO_FPS"] = "10"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    # Asegura que settings/engine se relean con el entorno de test.
    from iceberg_accesodatos import get_settings, reset_engine

    get_settings.cache_clear()
    reset_engine()

    from iceberg_api.main import app

    with TestClient(app) as test_client:
        yield test_client
