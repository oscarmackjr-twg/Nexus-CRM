from __future__ import annotations

import math
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Company, Deal, DealFunding, RefData, User
from backend.schemas.funding import (
    DealFundingCreate,
    DealFundingListResponse,
    DealFundingResponse,
    DealFundingUpdate,
)

StatusRef = aliased(RefData)
ProviderCompany = aliased(Company)


class DealFundingService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
        deal = await self.db.scalar(
            select(Deal).where(
                Deal.id == deal_id,
                Deal.org_id == self.current_user.org_id,
            )
        )
        if deal is None:
            raise HTTPException(status_code=404, detail="Deal not found")
        return deal

    def _base_stmt(self, deal_id: UUID):
        return (
            select(
                DealFunding,
                ProviderCompany.name.label("capital_provider_name"),
                StatusRef.label.label("status_label"),
            )
            .outerjoin(ProviderCompany, ProviderCompany.id == DealFunding.capital_provider_id)
            .outerjoin(StatusRef, StatusRef.id == DealFunding.status_id)
            .where(
                DealFunding.deal_id == deal_id,
                DealFunding.org_id == self.current_user.org_id,
            )
        )

    @staticmethod
    def _funding_response(row) -> DealFundingResponse:
        entry: DealFunding = row[0]

        def _decimal_to_float(v) -> float | None:
            if v is None:
                return None
            return float(v) if isinstance(v, Decimal) else v

        return DealFundingResponse(
            **{
                c.key: getattr(entry, c.key)
                for c in DealFunding.__table__.columns
                if c.key not in (
                    "projected_commitment_amount",
                    "actual_commitment_amount",
                )
            },
            projected_commitment_amount=_decimal_to_float(entry.projected_commitment_amount),
            actual_commitment_amount=_decimal_to_float(entry.actual_commitment_amount),
            capital_provider_name=row.capital_provider_name,
            status_label=row.status_label,
        )

    async def list_for_deal(
        self,
        deal_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> DealFundingListResponse:
        await self._get_deal_or_404(deal_id)

        count_stmt = select(func.count()).select_from(DealFunding).where(
            DealFunding.deal_id == deal_id,
            DealFunding.org_id == self.current_user.org_id,
        )
        total = (await self.db.scalar(count_stmt)) or 0

        stmt = (
            self._base_stmt(deal_id)
            .order_by(DealFunding.created_at.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = (await self.db.execute(stmt)).all()
        items = [self._funding_response(row) for row in rows]

        return DealFundingListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=max(1, math.ceil(total / size)),
        )

    async def create(self, deal_id: UUID, data: DealFundingCreate) -> DealFundingResponse:
        await self._get_deal_or_404(deal_id)

        entry = DealFunding(
            org_id=self.current_user.org_id,
            deal_id=deal_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **data.model_dump(exclude_unset=True),
        )
        self.db.add(entry)
        await self.db.flush()

        stmt = self._base_stmt(deal_id).where(DealFunding.id == entry.id)
        row = (await self.db.execute(stmt)).one()
        return self._funding_response(row)

    async def update(
        self,
        deal_id: UUID,
        funding_id: UUID,
        data: DealFundingUpdate,
    ) -> DealFundingResponse:
        await self._get_deal_or_404(deal_id)

        entry = await self.db.scalar(
            select(DealFunding).where(
                DealFunding.id == funding_id,
                DealFunding.deal_id == deal_id,
                DealFunding.org_id == self.current_user.org_id,
            )
        )
        if entry is None:
            raise HTTPException(status_code=404, detail="Funding entry not found")

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(entry, k, v)
        entry.updated_by = self.current_user.id
        await self.db.flush()

        stmt = self._base_stmt(deal_id).where(DealFunding.id == funding_id)
        row = (await self.db.execute(stmt)).one()
        return self._funding_response(row)

    async def delete(self, deal_id: UUID, funding_id: UUID) -> None:
        await self._get_deal_or_404(deal_id)

        entry = await self.db.scalar(
            select(DealFunding).where(
                DealFunding.id == funding_id,
                DealFunding.deal_id == deal_id,
                DealFunding.org_id == self.current_user.org_id,
            )
        )
        if entry is None:
            raise HTTPException(status_code=404, detail="Funding entry not found")

        await self.db.delete(entry)
        await self.db.flush()
