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


def test_video_genera_mp4(client):
    """Pipeline completo con TTS 'silent' (conftest): debe devolver un .mp4 real."""
    resp = client.post(
        "/video",
        json={
            "iceberg_title": "Curiosidades",
            "level_number": 1,
            "level_name": "La superficie",
            "entry_title": "El mar tiene ríos",
            "description": "Corrientes salinas bajo el océano.",
            "media": [],
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "video/mp4"
    # Firma de contenedor MP4: el box 'ftyp' aparece en los primeros bytes.
    assert b"ftyp" in resp.content[:64]
    assert len(resp.content) > 10_000


def test_narracion():
    from iceberg_dto import VideoRequest
    from iceberg_negocio.video import NarrationBuilder

    req = VideoRequest(
        iceberg_title="Curiosidades del océano",
        level_number=2,
        level_name="Profundo",
        entry_title="El mar tiene ríos",
        description="Corrientes salinas.",
        media=[],
    )
    guion = NarrationBuilder().build(req)
    assert guion == (
        "Curiosidades del océano. Nivel 2: Profundo. El mar tiene ríos. Corrientes salinas."
    )
