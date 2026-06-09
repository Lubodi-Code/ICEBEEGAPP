"""Smoke tests del backend: health + flujo iceberg->level->entry->media + público + video."""

from __future__ import annotations

import io

from PIL import Image


def _png_bytes() -> bytes:
    """Genera un PNG pequeño en memoria para la subida de media."""
    img = Image.new("RGB", (24, 24), color=(10, 80, 160))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_flujo_completo_y_publico(client):
    # 1) Crear iceberg
    resp = client.post("/icebergs", json={"titulo": "Curiosidades del océano"})
    assert resp.status_code == 201, resp.text
    ice = resp.json()
    slug = ice["slug"]
    iceberg_id = ice["id"]
    assert slug

    # 2) Crear nivel
    resp = client.post(
        f"/icebergs/{iceberg_id}/levels",
        json={"numero": 1, "nombre": "La superficie", "orden": 0},
    )
    assert resp.status_code == 201, resp.text
    level_id = resp.json()["id"]

    # 3) Crear entrada
    resp = client.post(
        f"/levels/{level_id}/entries",
        json={"titulo": "El mar tiene ríos", "descripcion": "Corrientes salinas.", "orden": 0},
    )
    assert resp.status_code == 201, resp.text
    entry_id = resp.json()["id"]

    # 4) Subir media (PNG -> se comprime a WebP)
    resp = client.post(
        f"/entries/{entry_id}/media",
        files={"file": ("foto.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 201, resp.text
    media = resp.json()
    assert media["tipo"] == "image"
    assert media["url"]

    # 5) Leer el grafo completo por slug
    resp = client.get(f"/icebergs/{slug}")
    assert resp.status_code == 200, resp.text
    graph = resp.json()
    assert graph["levels"][0]["entries"][0]["media"][0]["id"] == media["id"]

    # 6) Página pública con OG tags
    resp = client.get(f"/i/{slug}")
    assert resp.status_code == 200
    assert "og:title" in resp.text
    assert "Curiosidades del océano" in resp.text


def test_video_no_implementado(client):
    resp = client.post(
        "/video",
        json={
            "iceberg_title": "X",
            "level_number": 1,
            "level_name": None,
            "entry_title": "Y",
            "description": "Z",
            "media": [],
        },
    )
    assert resp.status_code == 501
    assert resp.json()["detail"] == "Pipeline de video aún no implementado"
