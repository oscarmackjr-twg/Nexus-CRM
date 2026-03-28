from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import User
from backend.schemas.counterparties import (
    DealCounterpartyCreate,
    DealCounterpartyListResponse,
    DealCounterpartyResponse,
    DealCounterpartyUpdate,
)
from backend.services.counterparties import DealCounterpartyService

router = APIRouter(prefix="/deals/{deal_id}/counterparties", tags=["counterparties"])


@router.get("/", response_model=DealCounterpartyListResponse)
async def list_counterparties(
    deal_id: UUID,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyListResponse:
    return await DealCounterpartyService(db, current_user).list_for_deal(deal_id, page=page, size=size)


@router.post("/", response_model=DealCounterpartyResponse, status_code=status.HTTP_201_CREATED)
async def create_counterparty(
    deal_id: UUID,
    payload: DealCounterpartyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyResponse:
    return await DealCounterpartyService(db, current_user).create(deal_id, payload)


@router.patch("/{counterparty_id}", response_model=DealCounterpartyResponse)
async def update_counterparty(
    deal_id: UUID,
    counterparty_id: UUID,
    payload: DealCounterpartyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealCounterpartyResponse:
    return await DealCounterpartyService(db, current_user).update(deal_id, counterparty_id, payload)


@router.delete("/{counterparty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_counterparty(
    deal_id: UUID,
    counterparty_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await DealCounterpartyService(db, current_user).delete(deal_id, counterparty_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
