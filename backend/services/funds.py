from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Fund, RefData, User
from backend.schemas.funds import FundCreate, FundResponse, FundUpdate

FundStatusRef = aliased(RefData)


class FundService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def list_funds(self) -> list[FundResponse]:
        stmt = (
            select(Fund, FundStatusRef.label.label("fundraise_status_label"))
            .outerjoin(FundStatusRef, FundStatusRef.id == Fund.fundraise_status_id)
            .where(Fund.org_id == self.current_user.org_id)
            .order_by(Fund.fund_name)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            FundResponse(
                **{c.key: getattr(row[0], c.key) for c in Fund.__table__.columns},
                fundraise_status_label=row.fundraise_status_label,
            )
            for row in rows
        ]

    async def create_fund(self, payload: FundCreate) -> FundResponse:
        fund = Fund(
            org_id=self.current_user.org_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **payload.model_dump(exclude_unset=True),
        )
        self.db.add(fund)
        await self.db.flush()
        await self.db.refresh(fund)
        # Re-query with label join
        return (await self.list_funds_by_ids([fund.id]))[0]

    async def update_fund(self, fund_id: UUID, payload: FundUpdate) -> FundResponse:
        fund = await self.db.scalar(
            select(Fund).where(Fund.id == fund_id, Fund.org_id == self.current_user.org_id)
        )
        if fund is None:
            raise HTTPException(status_code=404, detail="Fund not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(fund, k, v)
        fund.updated_by = self.current_user.id
        await self.db.flush()
        await self.db.refresh(fund)
        return (await self.list_funds_by_ids([fund.id]))[0]

    async def list_funds_by_ids(self, ids: list) -> list[FundResponse]:
        stmt = (
            select(Fund, FundStatusRef.label.label("fundraise_status_label"))
            .outerjoin(FundStatusRef, FundStatusRef.id == Fund.fundraise_status_id)
            .where(Fund.id.in_(ids))
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            FundResponse(
                **{c.key: getattr(row[0], c.key) for c in Fund.__table__.columns},
                fundraise_status_label=row.fundraise_status_label,
            )
            for row in rows
        ]
