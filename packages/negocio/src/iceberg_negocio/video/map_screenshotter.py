"""Captura una screenshot real del editor (modo mapa) con Playwright headless.

La intro del video puede usar la apariencia real de la SPA en vez del mapa
dibujado con Pillow: se abre ``#/e/<slug>?map=<entry_id>`` en un Chromium
headless, se espera a que la página esté lista y se toma una foto del viewport.
Se localiza el nivel/entrada objetivo para saber hacia dónde hacer zoom.

Si Playwright no está instalado o el frontend no responde, se lanza una
excepción y el renderer cae al mapa dibujado (``_draw_levels_map``).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote


def capture_map(
    slug: str,
    entry_id: str,
    frontend_url: str,
    out_path: Path,
    *,
    width: int = 720,
    height: int = 1280,
    scale: int = 2,
    timeout_ms: int = 20000,
) -> tuple[Path, float, float, float]:
    """Abre el editor en modo mapa y devuelve la screenshot y el foco del zoom.

    Returns:
        ``(ruta_png, centro_x, centro_y, alto_banda)`` en píxeles de la imagen
        hi-res (viewport * ``scale``). El centro apunta a la ficha de la entrada
        elegida y el alto corresponde a la banda de su nivel.
    """
    from playwright.sync_api import sync_playwright

    url = f"{frontend_url.rstrip('/')}/#/e/{quote(slug)}?map={quote(str(entry_id))}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=scale,
            )
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            # La SPA marca esta bandera cuando los datos y la imagen de fondo
            # del modo mapa ya están renderizados.
            page.wait_for_selector("[data-map-ready='true']", timeout=timeout_ms)
            page.screenshot(path=str(out_path), full_page=False)

            target = page.query_selector("[data-target='true']")  # ficha de la entrada
            band = page.query_selector("[data-target-band='true']")  # banda del nivel
            target_box = target.bounding_box() if target else None
            band_box = band.bounding_box() if band else None
        finally:
            browser.close()

    # bounding_box() entrega CSS px; la screenshot está a ``scale`` -> reescalar.
    focus = target_box or band_box
    if focus is not None:
        xc = (focus["x"] + focus["width"] / 2) * scale
        yc = (focus["y"] + focus["height"] / 2) * scale
    else:
        xc, yc = width * scale / 2.0, height * scale / 2.0

    if band_box is not None:
        band_h = band_box["height"] * scale
    elif target_box is not None:
        band_h = target_box["height"] * scale * 3.0  # aprox. la banda alrededor
    else:
        band_h = height * scale * 0.3

    return out_path, xc, yc, band_h
