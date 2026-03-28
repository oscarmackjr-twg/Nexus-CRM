from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import User
from backend.schemas.funding import (
    DealFundingCreate,
    DealFundingListResponse,
    DealFundingResponse,
    DealFundingUpdate,
)
from backend.services.funding import DealFundingService

router = APIRouter(prefix="/deals/{deal_id}/funding", tags=["funding"])


@router.get("/", response_model=DealFundingListResponse)
async def list_funding(
    deal_id: UUID,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealFundingListResponse:
    return await DealFundingService(db, current_user).list_for_deal(deal_id, page=page, size=size)


@router.post("/", response_model=DealFundingResponse, status_code=status.HTTP_201_CREATED)
async def create_funding(
    deal_id: UUID,
    payload: DealFundingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealFundingResponse:
    result = await DealFundingService(db, current_user).create(deal_id, payload)
    await db.commit()
    return result


@router.patch("/{funding_id}", response_model=DealFundingResponse)
async def update_funding(
    deal_id: UUID,
    funding_id: UUID,
    payload: DealFundingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealFundingResponse:
    result = await DealFundingService(db, current_user).update(deal_id, funding_id, payload)
    await db.commit()
    return result


@router.delete("/{funding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_funding(
    deal_id: UUID,
    funding_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await DealFundingService(db, current_user).delete(deal_id, funding_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
