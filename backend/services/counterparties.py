from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Company, Deal, DealCounterparty, RefData, User
from backend.schemas.counterparties import (
    DealCounterpartyCreate,
    DealCounterpartyListResponse,
    DealCounterpartyResponse,
    DealCounterpartyUpdate,
)
from backend.services._crm import clamp_pagination, count_rows, page_count

# Aliases for multi-join disambiguation
TierRef = aliased(RefData)
InvestorTypeRef = aliased(RefData)
CpartyCompany = aliased(Company)


class DealCounterpartyService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def _base_stmt(self, deal_id: UUID):
        stmt = (
            select(
                DealCounterparty,
                CpartyCompany.name.label("company_name"),
                TierRef.label.label("tier_label"),
                InvestorTypeRef.label.label("investor_type_label"),
            )
            .outerjoin(CpartyCompany, CpartyCompany.id == DealCounterparty.company_id)
            .outerjoin(TierRef, TierRef.id == DealCounterparty.tier_id)
            .outerjoin(InvestorTypeRef, InvestorTypeRef.id == DealCounterparty.investor_type_id)
            .where(
                DealCounterparty.deal_id == deal_id,
                DealCounterparty.org_id == self.current_user.org_id,
            )
        )
        return stmt

    @staticmethod
    def _counterparty_response(row) -> DealCounterpartyResponse:
        cp = row[0]
        return DealCounterpartyResponse(
            id=cp.id,
            org_id=cp.org_id,
            deal_id=cp.deal_id,
            company_id=cp.company_id,
            company_name=row.company_name,
            primary_contact_name=cp.primary_contact_name,
            primary_contact_email=cp.primary_contact_email,
            primary_contact_phone=cp.primary_contact_phone,
            nda_sent_at=cp.nda_sent_at,
            nda_signed_at=cp.nda_signed_at,
            nrl_signed_at=cp.nrl_signed_at,
            intro_materials_sent_at=cp.intro_materials_sent_at,
            vdr_access_granted_at=cp.vdr_access_granted_at,
            feedback_received_at=cp.feedback_received_at,
            tier_id=cp.tier_id,
            tier_label=row.tier_label,
            investor_type_id=cp.investor_type_id,
            investor_type_label=row.investor_type_label,
            check_size_amount=float(cp.check_size_amount) if cp.check_size_amount is not None else None,
            check_size_currency=cp.check_size_currency,
            aum_amount=float(cp.aum_amount) if cp.aum_amount is not None else None,
            aum_currency=cp.aum_currency,
            next_steps=cp.next_steps,
            notes=cp.notes,
            position=cp.position,
            created_at=cp.created_at,
            updated_at=cp.updated_at,
        )

    async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
        result = await self.db.execute(
            select(Deal).where(
                Deal.id == deal_id,
                Deal.org_id == self.current_user.org_id,
            )
        )
        deal = result.scalar_one_or_none()
        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        return deal

    async def list_for_deal(
        self,
        deal_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> DealCounterpartyListResponse:
        page, size = clamp_pagination(page, size)
        base = self._base_stmt(deal_id)
        total = await count_rows(self.db, base)
        stmt = (
            base
            .order_by(DealCounterparty.position.asc().nullslast(), DealCounterparty.created_at.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return DealCounterpartyListResponse(
            items=[self._counterparty_response(r) for r in rows],
            total=total,
            page=page,
            size=size,
            pages=page_count(total, size),
        )

    async def create(self, deal_id: UUID, data: DealCounterpartyCreate) -> DealCounterpartyResponse:
        await self._get_deal_or_404(deal_id)
        cp = DealCounterparty(
            org_id=self.current_user.org_id,
            deal_id=deal_id,
            **data.model_dump(exclude_unset=False),
        )
        self.db.add(cp)
        await self.db.flush()
        await self.db.commit()
        # Re-query with joined labels
        result = await self.db.execute(
            self._base_stmt(deal_id).where(DealCounterparty.id == cp.id)
        )
        row = result.one()
        return self._counterparty_response(row)

    async def update(
        self,
        deal_id: UUID,
        counterparty_id: UUID,
        data: DealCounterpartyUpdate,
    ) -> DealCounterpartyResponse:
        result = await self.db.execute(
            select(DealCounterparty).where(
                DealCounterparty.id == counterparty_id,
                DealCounterparty.deal_id == deal_id,
                DealCounterparty.org_id == self.current_user.org_id,
            )
        )
        cp = result.scalar_one_or_none()
        if cp is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counterparty not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cp, field, value)
        await self.db.commit()
        # Re-query with joined labels
        result = await self.db.execute(
            self._base_stmt(deal_id).where(DealCounterparty.id == cp.id)
        )
        row = result.one()
        return self._counterparty_response(row)

    async def delete(self, deal_id: UUID, counterparty_id: UUID) -> None:
        result = await self.db.execute(
            select(DealCounterparty).where(
                DealCounterparty.id == counterparty_id,
                DealCounterparty.deal_id == deal_id,
                DealCounterparty.org_id == self.current_user.org_id,
            )
        )
        cp = result.scalar_one_or_none()
        if cp is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counterparty not found")
        await self.db.delete(cp)
        await self.db.commit()
