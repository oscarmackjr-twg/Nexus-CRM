from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Company, Contact, Deal, RefData, User
from backend.schemas.companies import CompanyCreate, CompanyListResponse, CompanyResponse, CompanyUpdate
from backend.schemas.contacts import ContactResponse
from backend.schemas.deals import DealResponse
from backend.services._crm import (
    accessible_team_ids,
    apply_tag_filter,
    clamp_pagination,
    contact_name_expr,
    count_rows,
    ensure_owner_or_admin,
    merge_custom_fields,
    page_count,
    user_name_expr,
)
from backend.services.contacts import ContactService
from backend.services.deals import DealService


class CompanyService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def _base_stmt(self):
        CompanyTypeRef = aliased(RefData)
        TierRef = aliased(RefData)
        SectorRef = aliased(RefData)
        SubSectorRef = aliased(RefData)
        CoverageUser = aliased(User)
        return (
            select(
                Company,
                user_name_expr().label("owner_name"),
                CompanyTypeRef.label.label("company_type_label"),
                TierRef.label.label("tier_label"),
                SectorRef.label.label("sector_label"),
                SubSectorRef.label.label("sub_sector_label"),
                func.coalesce(CoverageUser.full_name, CoverageUser.username).label("coverage_person_name"),
            )
            .outerjoin(User, User.id == Company.owner_id)
            .outerjoin(CompanyTypeRef, CompanyTypeRef.id == Company.company_type_id)
            .outerjoin(TierRef, TierRef.id == Company.tier_id)
            .outerjoin(SectorRef, SectorRef.id == Company.sector_id)
            .outerjoin(SubSectorRef, SubSectorRef.id == Company.sub_sector_id)
            .outerjoin(CoverageUser, CoverageUser.id == Company.coverage_person_id)
            .where(Company.org_id == self.current_user.org_id)
        )

    @staticmethod
    def _company_response(row, linked_contacts_count: int | None = None, open_deals_count: int | None = None) -> CompanyResponse:
        company = row[0]
        return CompanyResponse(
            id=company.id,
            org_id=company.org_id,
            name=company.name,
            domain=company.domain,
            industry=company.industry,
            size_range=company.size_range,
            annual_revenue=float(company.annual_revenue) if company.annual_revenue is not None else None,
            website=company.website,
            linkedin_company_id=company.linkedin_company_id,
            linkedin_synced_at=company.linkedin_synced_at,
            owner_id=company.owner_id,
            owner_name=row.owner_name,
            tags=list(company.tags or []),
            custom_fields=dict(company.custom_fields or {}),
            is_archived=company.is_archived,
            created_at=company.created_at,
            updated_at=company.updated_at,
            linked_contacts_count=linked_contacts_count,
            open_deals_count=open_deals_count,
            # PE Blueprint fields
            company_type_id=str(company.company_type_id) if company.company_type_id else None,
            company_type_label=row.company_type_label,
            company_sub_type_ids=list(company.company_sub_type_ids or []),
            description=company.description,
            main_phone=company.main_phone,
            parent_company_id=str(company.parent_company_id) if company.parent_company_id else None,
            address=company.address,
            city=company.city,
            state=company.state,
            postal_code=company.postal_code,
            country=company.country,
            tier_id=str(company.tier_id) if company.tier_id else None,
            tier_label=row.tier_label,
            sector_id=str(company.sector_id) if company.sector_id else None,
            sector_label=row.sector_label,
            sub_sector_id=str(company.sub_sector_id) if company.sub_sector_id else None,
            sub_sector_label=row.sub_sector_label,
            sector_preferences=list(company.sector_preferences or []),
            sub_sector_preferences=list(company.sub_sector_preferences or []),
            preference_notes=company.preference_notes,
            aum_amount=float(company.aum_amount) if company.aum_amount is not None else None,
            aum_currency=company.aum_currency,
            ebitda_amount=float(company.ebitda_amount) if company.ebitda_amount is not None else None,
            ebitda_currency=company.ebitda_currency,
            typical_bite_size_low=float(company.typical_bite_size_low) if company.typical_bite_size_low is not None else None,
            typical_bite_size_high=float(company.typical_bite_size_high) if company.typical_bite_size_high is not None else None,
            bite_size_currency=company.bite_size_currency,
            co_invest=company.co_invest,
            target_deal_size_id=str(company.target_deal_size_id) if company.target_deal_size_id else None,
            transaction_types=list(company.transaction_types or []),
            min_ebitda=float(company.min_ebitda) if company.min_ebitda is not None else None,
            max_ebitda=float(company.max_ebitda) if company.max_ebitda is not None else None,
            ebitda_range_currency=company.ebitda_range_currency,
            watchlist=company.watchlist,
            coverage_person_id=str(company.coverage_person_id) if company.coverage_person_id else None,
            coverage_person_name=row.coverage_person_name,
            contact_frequency=company.contact_frequency,
            legacy_id=company.legacy_id,
        )

    async def list_companies(
        self,
        page: int = 1,
        size: int = 25,
        search: str | None = None,
        industry: str | None = None,
        size_range: str | None = None,
        owner_id: UUID | None = None,
        tags: list[str] | None = None,
        include_archived: bool = False,
    ) -> CompanyListResponse:
        page, size = clamp_pagination(page, size)
        stmt = self._base_stmt()
        if not include_archived:
            stmt = stmt.where(Company.is_archived.is_(False))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(or_(Company.name.ilike(term), Company.domain.ilike(term), Company.website.ilike(term)))
        if industry:
            stmt = stmt.where(Company.industry == industry)
        if size_range:
            stmt = stmt.where(Company.size_range == size_range)
        if owner_id:
            stmt = stmt.where(Company.owner_id == owner_id)
        stmt = apply_tag_filter(stmt, Company.tags, tags)
        total = await count_rows(self.db, stmt)
        rows = (
            await self.db.execute(
                stmt.order_by(Company.created_at.desc()).offset((page - 1) * size).limit(size)
            )
        ).all()
        return CompanyListResponse(
            items=[self._company_response(row) for row in rows],
            total=total,
            page=page,
            size=size,
            pages=page_count(total, size),
        )

    async def get_company(self, company_id: UUID) -> CompanyResponse:
        row = (await self.db.execute(self._base_stmt().where(Company.id == company_id))).first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        linked_contacts_count = int(
            (await self.db.scalar(select(func.count()).select_from(Contact).where(Contact.company_id == company_id))) or 0
        )
        open_deals_count = int(
            (
                await self.db.scalar(
                    select(func.count()).select_from(Deal).where(Deal.company_id == company_id, Deal.status == "open")
                )
            )
            or 0
        )
        return self._company_response(row, linked_contacts_count=linked_contacts_count, open_deals_count=open_deals_count)

    async def create_company(self, data: CompanyCreate) -> CompanyResponse:
        company = Company(
            org_id=self.current_user.org_id,
            name=data.name,
            domain=data.domain,
            industry=data.industry,
            size_range=data.size_range,
            annual_revenue=data.annual_revenue,
            website=data.website,
            owner_id=self.current_user.id,
            tags=data.tags,
            custom_fields=data.custom_fields,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        # PE Blueprint fields
        for field in [
            "company_type_id", "company_sub_type_ids", "description", "main_phone",
            "parent_company_id", "address", "city", "state", "postal_code", "country",
            "tier_id", "sector_id", "sub_sector_id", "sector_preferences",
            "sub_sector_preferences", "preference_notes", "aum_amount", "aum_currency",
            "ebitda_amount", "ebitda_currency", "typical_bite_size_low",
            "typical_bite_size_high", "bite_size_currency", "co_invest",
            "target_deal_size_id", "transaction_types", "min_ebitda", "max_ebitda",
            "ebitda_range_currency", "watchlist", "coverage_person_id",
            "contact_frequency", "legacy_id",
        ]:
            value = getattr(data, field, None)
            if value is not None:
                setattr(company, field, value)
        self.db.add(company)
        await self.db.commit()
        return await self.get_company(company.id)

    async def update_company(self, company_id: UUID, data: CompanyUpdate) -> CompanyResponse:
        company = await self.db.scalar(select(Company).where(Company.id == company_id, Company.org_id == self.current_user.org_id))
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        ensure_owner_or_admin(company.owner_id, self.current_user)
        for field in ["name", "domain", "industry", "size_range", "annual_revenue", "website"]:
            value = getattr(data, field)
            if value is not None:
                setattr(company, field, value)
        if data.owner_id is not None:
            owner = await self.db.scalar(select(User).where(User.id == data.owner_id, User.org_id == self.current_user.org_id))
            if owner is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner not found")
            company.owner_id = owner.id
        if data.tags is not None:
            company.tags = data.tags
        if data.custom_fields is not None:
            company.custom_fields = merge_custom_fields(company.custom_fields, data.custom_fields)
        # PE Blueprint fields — scalar fields
        for field in [
            "company_type_id", "description", "main_phone", "parent_company_id",
            "address", "city", "state", "postal_code", "country",
            "tier_id", "sector_id", "sub_sector_id", "preference_notes",
            "aum_amount", "aum_currency", "ebitda_amount", "ebitda_currency",
            "typical_bite_size_low", "typical_bite_size_high", "bite_size_currency",
            "co_invest", "target_deal_size_id", "min_ebitda", "max_ebitda",
            "ebitda_range_currency", "watchlist", "coverage_person_id",
            "contact_frequency", "legacy_id",
        ]:
            value = getattr(data, field, None)
            if value is not None:
                setattr(company, field, value)
        # JSONB list fields — direct assignment replaces the array
        if data.company_sub_type_ids is not None:
            company.company_sub_type_ids = data.company_sub_type_ids
        if data.sector_preferences is not None:
            company.sector_preferences = data.sector_preferences
        if data.sub_sector_preferences is not None:
            company.sub_sector_preferences = data.sub_sector_preferences
        if data.transaction_types is not None:
            company.transaction_types = data.transaction_types
        company.updated_by = self.current_user.id
        await self.db.commit()
        return await self.get_company(company.id)

    async def delete_company(self, company_id: UUID) -> None:
        company = await self.db.scalar(select(Company).where(Company.id == company_id, Company.org_id == self.current_user.org_id))
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        ensure_owner_or_admin(company.owner_id, self.current_user)
        company.is_archived = True
        await self.db.commit()

    async def get_company_contacts(self, company_id: UUID) -> list[ContactResponse]:
        company = await self.db.scalar(select(Company).where(Company.id == company_id, Company.org_id == self.current_user.org_id))
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        rows = (
            await self.db.execute(
                ContactService(self.db, self.current_user)
                ._base_stmt()
                .where(Contact.company_id == company_id, Contact.is_archived.is_(False))
                .order_by(Contact.created_at.desc())
            )
        ).all()
        return [ContactService._contact_response(row) for row in rows]

    async def get_company_deals(self, company_id: UUID) -> list[DealResponse]:
        company = await self.db.scalar(select(Company).where(Company.id == company_id, Company.org_id == self.current_user.org_id))
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        deal_service = DealService(self.db, self.current_user)
        visible_team_ids = await accessible_team_ids(self.db, self.current_user)
        stmt = deal_service._base_deal_stmt(visible_team_ids).where(Deal.company_id == company_id, Deal.is_private.is_(False))
        rows = (await self.db.execute(stmt.order_by(Deal.created_at.desc()))).all()
        return [deal_service._deal_response(row) for row in rows]
