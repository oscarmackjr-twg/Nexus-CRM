from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Company, Contact, ContactCoveragePerson, Deal, DealActivity, RefData, User
from backend.schemas.contacts import ContactCreate, ContactListResponse, ContactResponse, ContactUpdate
from backend.schemas.deals import ActivityResponse, DealResponse
from backend.services._crm import (
    accessible_team_ids,
    apply_tag_filter,
    clamp_pagination,
    contact_name_expr,
    count_rows,
    ensure_company_in_org,
    ensure_owner_or_admin,
    merge_custom_fields,
    page_count,
    user_name_expr,
)
from backend.services.deals import DealService


class ContactService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    @staticmethod
    def _contact_response(
        row,
        related_deal_count: int | None = None,
        recent_activity: list[ActivityResponse] | None = None,
        coverage_persons: list[dict] | None = None,
    ) -> ContactResponse:
        contact = row[0]
        return ContactResponse(
            id=contact.id,
            org_id=contact.org_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            title=contact.title,
            company_id=contact.company_id,
            company_name=row.company_name,
            linkedin_profile_url=contact.linkedin_profile_url,
            linkedin_member_id=contact.linkedin_member_id,
            linkedin_synced_at=contact.linkedin_synced_at,
            owner_id=contact.owner_id,
            owner_name=row.owner_name,
            lead_score=contact.lead_score,
            lifecycle_stage=contact.lifecycle_stage,
            tags=list(contact.tags or []),
            custom_fields=dict(contact.custom_fields or {}),
            is_archived=contact.is_archived,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
            # PE Blueprint fields
            business_phone=contact.business_phone,
            mobile_phone=contact.mobile_phone,
            assistant_name=contact.assistant_name,
            assistant_email=contact.assistant_email,
            assistant_phone=contact.assistant_phone,
            address=contact.address,
            city=contact.city,
            state=contact.state,
            postal_code=contact.postal_code,
            country=contact.country,
            contact_type_id=contact.contact_type_id,
            contact_type_label=row.contact_type_label,
            primary_contact=contact.primary_contact,
            contact_frequency=contact.contact_frequency,
            sector=list(contact.sector or []),
            sub_sector=list(contact.sub_sector or []),
            previous_employment=list(contact.previous_employment or []),
            board_memberships=list(contact.board_memberships or []),
            linkedin_url=contact.linkedin_url,
            legacy_id=contact.legacy_id,
            coverage_persons=coverage_persons if coverage_persons is not None else [],
            related_deal_count=related_deal_count,
            recent_activity=recent_activity,
        )

    def _base_stmt(self):
        ContactTypeRef = aliased(RefData)
        return (
            select(
                Contact,
                Company.name.label("company_name"),
                user_name_expr().label("owner_name"),
                ContactTypeRef.label.label("contact_type_label"),
            )
            .outerjoin(Company, Company.id == Contact.company_id)
            .outerjoin(User, User.id == Contact.owner_id)
            .outerjoin(ContactTypeRef, ContactTypeRef.id == Contact.contact_type_id)
            .where(Contact.org_id == self.current_user.org_id)
        )

    async def _load_coverage_persons(self, contact_id) -> list[dict]:
        stmt = (
            select(User.id, User.full_name)
            .join(ContactCoveragePerson, ContactCoveragePerson.user_id == User.id)
            .where(ContactCoveragePerson.contact_id == str(contact_id))
        )
        rows = (await self.db.execute(stmt)).all()
        return [{"id": str(r.id), "name": r.full_name} for r in rows]

    async def list_contacts(
        self,
        page: int = 1,
        size: int = 25,
        search: str | None = None,
        lifecycle_stage: str | None = None,
        company_id: UUID | None = None,
        owner_id: UUID | None = None,
        tags: list[str] | None = None,
        include_archived: bool = False,
    ) -> ContactListResponse:
        page, size = clamp_pagination(page, size)
        stmt = self._base_stmt()
        if not include_archived:
            stmt = stmt.where(Contact.is_archived.is_(False))
        if lifecycle_stage:
            stmt = stmt.where(Contact.lifecycle_stage == lifecycle_stage)
        if company_id:
            stmt = stmt.where(Contact.company_id == company_id)
        if owner_id:
            stmt = stmt.where(Contact.owner_id == owner_id)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    contact_name_expr().ilike(term),
                    Contact.email.ilike(term),
                    Contact.phone.ilike(term),
                    Company.name.ilike(term),
                )
            )
        stmt = apply_tag_filter(stmt, Contact.tags, tags)
        total = await count_rows(self.db, stmt)
        rows = (
            await self.db.execute(
                stmt.order_by(Contact.created_at.desc()).offset((page - 1) * size).limit(size)
            )
        ).all()
        return ContactListResponse(
            items=[self._contact_response(row, coverage_persons=[]) for row in rows],
            total=total,
            page=page,
            size=size,
            pages=page_count(total, size),
        )

    async def get_contact(self, contact_id: UUID) -> ContactResponse:
        row = (await self.db.execute(self._base_stmt().where(Contact.id == contact_id))).first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        related_deal_count = int(
            (
                await self.db.scalar(
                    select(func.count()).select_from(Deal).where(
                        Deal.contact_id == contact_id,
                        Deal.org_id == self.current_user.org_id,
                    )
                )
            )
            or 0
        )
        recent_activity = await self.get_contact_activities(contact_id, limit=5)
        coverage = await self._load_coverage_persons(contact_id)
        return self._contact_response(row, related_deal_count=related_deal_count, recent_activity=recent_activity, coverage_persons=coverage)

    async def create_contact(self, data: ContactCreate) -> ContactResponse:
        await ensure_company_in_org(self.db, self.current_user.org_id, data.company_id)
        contact = Contact(
            org_id=self.current_user.org_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=str(data.email) if data.email else None,
            phone=data.phone,
            title=data.title,
            company_id=data.company_id,
            owner_id=self.current_user.id,
            lifecycle_stage=data.lifecycle_stage,
            tags=data.tags,
            custom_fields=data.custom_fields,
            # PE Blueprint fields
            business_phone=data.business_phone,
            mobile_phone=data.mobile_phone,
            assistant_name=data.assistant_name,
            assistant_email=data.assistant_email,
            assistant_phone=data.assistant_phone,
            address=data.address,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            contact_type_id=data.contact_type_id,
            primary_contact=data.primary_contact,
            contact_frequency=data.contact_frequency,
            sector=data.sector,
            sub_sector=data.sub_sector,
            previous_employment=data.previous_employment,
            board_memberships=data.board_memberships,
            linkedin_url=data.linkedin_url,
            legacy_id=data.legacy_id,
        )
        self.db.add(contact)
        await self.db.flush()
        # Handle coverage_persons M2M
        if data.coverage_persons:
            for user_id in data.coverage_persons:
                self.db.add(ContactCoveragePerson(
                    contact_id=str(contact.id), user_id=str(user_id)
                ))
        await self.db.commit()
        return await self.get_contact(contact.id)

    async def update_contact(self, contact_id: UUID, data: ContactUpdate) -> ContactResponse:
        contact = await self.db.scalar(select(Contact).where(Contact.id == contact_id, Contact.org_id == self.current_user.org_id))
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        ensure_owner_or_admin(contact.owner_id, self.current_user)
        if data.company_id is not None:
            await ensure_company_in_org(self.db, self.current_user.org_id, data.company_id)
        for field in ["first_name", "last_name", "phone", "title", "lead_score", "lifecycle_stage", "company_id"]:
            value = getattr(data, field)
            if value is not None:
                setattr(contact, field, value)
        if data.email is not None:
            contact.email = str(data.email)
        if data.owner_id is not None:
            owner = await self.db.scalar(select(User).where(User.id == data.owner_id, User.org_id == self.current_user.org_id))
            if owner is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner not found")
            contact.owner_id = owner.id
        if data.tags is not None:
            contact.tags = data.tags
        if data.custom_fields is not None:
            contact.custom_fields = merge_custom_fields(contact.custom_fields, data.custom_fields)
        # PE Blueprint scalar fields
        for field in [
            "business_phone", "mobile_phone", "assistant_name", "assistant_email", "assistant_phone",
            "address", "city", "state", "postal_code", "country",
            "contact_type_id", "primary_contact", "contact_frequency",
            "linkedin_url", "legacy_id",
        ]:
            value = getattr(data, field)
            if value is not None:
                setattr(contact, field, value)
        # PE Blueprint JSONB fields (full replacement)
        if data.sector is not None:
            contact.sector = data.sector
        if data.sub_sector is not None:
            contact.sub_sector = data.sub_sector
        if data.previous_employment is not None:
            contact.previous_employment = data.previous_employment
        if data.board_memberships is not None:
            contact.board_memberships = data.board_memberships
        # Coverage persons M2M — delete + re-insert
        if data.coverage_persons is not None:
            await self.db.execute(
                delete(ContactCoveragePerson).where(
                    ContactCoveragePerson.contact_id == str(contact.id)
                )
            )
            for user_id in data.coverage_persons:
                self.db.add(ContactCoveragePerson(
                    contact_id=str(contact.id), user_id=str(user_id)
                ))
        await self.db.commit()
        return await self.get_contact(contact.id)

    async def delete_contact(self, contact_id: UUID) -> None:
        contact = await self.db.scalar(select(Contact).where(Contact.id == contact_id, Contact.org_id == self.current_user.org_id))
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        ensure_owner_or_admin(contact.owner_id, self.current_user)
        contact.is_archived = True
        await self.db.commit()

    async def get_contact_deals(self, contact_id: UUID) -> list[DealResponse]:
        contact = await self.db.scalar(select(Contact).where(Contact.id == contact_id, Contact.org_id == self.current_user.org_id))
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        deal_service = DealService(self.db, self.current_user)
        visible_team_ids = await accessible_team_ids(self.db, self.current_user)
        stmt = deal_service._base_deal_stmt(visible_team_ids).where(Deal.contact_id == contact_id)
        stmt = stmt.where(or_(Deal.is_private.is_(False), Deal.owner_id == self.current_user.id))
        rows = (await self.db.execute(stmt.order_by(Deal.created_at.desc()))).all()
        return [deal_service._deal_response(row) for row in rows]

    async def get_contact_activities(self, contact_id: UUID, limit: int = 20) -> list[ActivityResponse]:
        contact = await self.db.scalar(select(Contact).where(Contact.id == contact_id, Contact.org_id == self.current_user.org_id))
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        visible_team_ids = await accessible_team_ids(self.db, self.current_user)
        stmt = (
            select(DealActivity, user_name_expr().label("user_name"))
            .join(User, User.id == DealActivity.user_id)
            .outerjoin(Deal, Deal.id == DealActivity.deal_id)
            .where(
                or_(
                    DealActivity.contact_id == str(contact_id),
                    Deal.contact_id == contact_id,
                )
            )
            .where(or_(Deal.org_id == self.current_user.org_id, DealActivity.deal_id.is_(None)))
        )
        if visible_team_ids is not None:
            if not visible_team_ids:
                # Only show contact-level activities (no deal) when team scope is empty
                stmt = stmt.where(DealActivity.deal_id.is_(None))
            else:
                stmt = stmt.where(
                    or_(
                        DealActivity.deal_id.is_(None),
                        Deal.team_id.in_(visible_team_ids),
                    )
                )
        stmt = stmt.where(or_(DealActivity.is_private.is_(False), DealActivity.user_id == self.current_user.id))
        rows = (await self.db.execute(stmt.order_by(DealActivity.occurred_at.desc()).limit(limit))).all()
        return [DealService._activity_response(row) for row in rows]

    async def log_contact_activity(self, contact_id: UUID, activity_type: str, notes: str | None, occurred_at, deal_id: UUID | None = None) -> DealActivity:
        contact = await self.db.scalar(select(Contact).where(Contact.id == contact_id, Contact.org_id == self.current_user.org_id))
        if contact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        activity = DealActivity(
            deal_id=deal_id,
            contact_id=str(contact_id),
            user_id=self.current_user.id,
            activity_type=activity_type,
            body=notes,
            occurred_at=occurred_at,
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity
