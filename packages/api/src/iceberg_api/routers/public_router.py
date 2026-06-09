"""Router público: página con OG tags (el gancho), renderizada con Jinja2."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from iceberg_api.deps import IcebergServiceDep, ShareServiceDep

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["public"])


@router.get("/i/{slug}", response_class=HTMLResponse)
def public_iceberg(
    slug: str,
    request: Request,
    service: IcebergServiceDep,
    share: ShareServiceDep,
) -> HTMLResponse:
    ice = service.get_public(slug)
    og = share.build_og_meta(ice)
    return templates.TemplateResponse(
        request,
        "iceberg.html",
        {"ice": ice, "og": og},
    )
