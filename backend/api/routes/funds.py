from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.security import get_current_user
from backend.database import get_db_session
from backend.models import User
from backend.schemas.funds import FundCreate, FundResponse, FundUpdate
from backend.services.funds import FundService

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("", response_model=list[FundResponse])
async def list_funds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[FundResponse]:
    return await FundService(db, current_user).list_funds()


@router.post("", response_model=FundResponse)
async def create_fund(
    payload: FundCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FundResponse:
    result = await FundService(db, current_user).create_fund(payload)
    await db.commit()
    return result


@router.patch("/{fund_id}", response_model=FundResponse)
async def update_fund(
    fund_id: UUID,
    payload: FundUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> FundResponse:
    result = await FundService(db, current_user).update_fund(fund_id, payload)
    await db.commit()
    return result
