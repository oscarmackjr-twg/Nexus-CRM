from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_db, require_role
from backend.models import User
from backend.schemas.ref_data import RefDataCreate, RefDataResponse, RefDataUpdate
from backend.services.ref_data import RefDataService

router = APIRouter(prefix="/admin/ref-data", tags=["admin"])


@router.get("/", response_model=list[RefDataResponse])
async def list_ref_data(
    category: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RefDataResponse]:
    return await RefDataService(db, current_user).list_by_category(
        category, include_inactive=include_inactive
    )


@router.post("/", response_model=RefDataResponse, status_code=status.HTTP_201_CREATED)
async def create_ref_data(
    payload: RefDataCreate,
    current_user: User = Depends(require_role("org_admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> RefDataResponse:
    return await RefDataService(db, current_user).create(payload)


@router.patch("/{item_id}", response_model=RefDataResponse)
async def update_ref_data(
    item_id: UUID,
    payload: RefDataUpdate,
    current_user: User = Depends(require_role("org_admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> RefDataResponse:
    return await RefDataService(db, current_user).update(item_id, payload)
