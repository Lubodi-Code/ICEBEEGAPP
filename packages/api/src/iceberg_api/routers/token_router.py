"""Router de EDIT_TOKEN: enlaces de edición compartibles."""

from __future__ import annotations

from fastapi import APIRouter, status

from iceberg_api.deps import EditTokenServiceDep
from iceberg_dto import EditTokenRead, EditTokenValidation

router = APIRouter(tags=["edit-tokens"])


@router.post(
    "/icebergs/{iceberg_id}/edit-token",
    response_model=EditTokenRead,
    status_code=status.HTTP_201_CREATED,
)
def create_edit_token(iceberg_id: str, service: EditTokenServiceDep) -> EditTokenRead:
    return service.create(iceberg_id)


@router.get(
    "/icebergs/{iceberg_id}/edit-token/validate",
    response_model=EditTokenValidation,
)
def validate_edit_token(
    iceberg_id: str, token: str, service: EditTokenServiceDep
) -> EditTokenValidation:
    return service.validate(iceberg_id, token)
