from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from backend.models import Company, Contact, Deal, DealActivity, DealTeamMember, Fund, Pipeline, PipelineStage, RefData, Team, User
from backend.schemas.deals import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    DealCreate,
    DealListResponse,
    DealMoveStage,
    DealResponse,
    DealUpdate,
)
from backend.database import get_engine
from backend.services._crm import (
    accessible_team_ids,
    apply_tag_filter,
    clamp_pagination,
    contact_name_expr,
    count_rows,
    deal_activity_subqueries,
    ensure_company_in_org,
    ensure_contact_in_org,
    ensure_team_in_org,
    is_admin,
    is_manager_plus,
    merge_custom_fields,
    page_count,
    private_deal_predicate,
    user_name_expr,
    utcnow,
)

# Aliases for multi-join disambiguation (PE fields)
TxnType = aliased(RefData)
SourceType = aliased(RefData)
SourceCompany = aliased(Company)
PlatformCompany = aliased(Company)
SourceContact = aliased(Contact)
OriginatorUser = aliased(User)


class DealService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    async def _visible_team_ids(self) -> set[UUID] | None:
        return await accessible_team_ids(self.db, self.current_user)

    def _base_deal_stmt(self, visible_team_ids: set[UUID] | None):
        dialect_name = get_engine().dialect.name
        _, _, days_in_stage, is_rotting = deal_activity_subqueries(dialect_name)
        owner_name = user_name_expr().label("owner_name")
        contact_name = contact_name_expr().label("contact_name")
        source_individual_name = func.trim(
            func.coalesce(SourceContact.first_name, literal(""))
            + literal(" ")
            + func.coalesce(SourceContact.last_name, literal(""))
        ).label("source_individual_name")
        stmt = (
            select(
                Deal,
                Pipeline.name.label("pipeline_name"),
                PipelineStage.name.label("stage_name"),
                owner_name,
                contact_name,
                Company.name.label("company_name"),
                days_in_stage.label("days_in_stage"),
                is_rotting.label("is_rotting"),
                # PE label fields
                TxnType.label.label("transaction_type_label"),
                SourceType.label.label("source_type_label"),
                Fund.fund_name.label("fund_name"),
                SourceCompany.name.label("source_company_name"),
                PlatformCompany.name.label("platform_company_name"),
                func.coalesce(OriginatorUser.full_name, OriginatorUser.username).label("originator_name"),
                source_individual_name,
            )
            .join(Pipeline, Pipeline.id == Deal.pipeline_id)
            .join(PipelineStage, PipelineStage.id == Deal.stage_id)
            .join(User, User.id == Deal.owner_id)
            .outerjoin(Contact, Contact.id == Deal.contact_id)
            .outerjoin(Company, Company.id == Deal.company_id)
            # PE aliased joins
            .outerjoin(TxnType, TxnType.id == Deal.transaction_type_id)
            .outerjoin(SourceType, SourceType.id == Deal.source_type_id)
            .outerjoin(Fund, Fund.id == Deal.fund_id)
            .outerjoin(SourceCompany, SourceCompany.id == Deal.source_company_id)
            .outerjoin(PlatformCompany, PlatformCompany.id == Deal.platform_company_id)
            .outerjoin(OriginatorUser, OriginatorUser.id == Deal.originator_id)
            .outerjoin(SourceContact, SourceContact.id == Deal.source_individual_id)
            .where(Deal.org_id == self.current_user.org_id)
        )
        if visible_team_ids is not None:
            if not visible_team_ids:
                stmt = stmt.where(False)
            else:
                stmt = stmt.where(Deal.team_id.in_(visible_team_ids))
        stmt = stmt.where(private_deal_predicate(self.current_user, visible_team_ids))
        return stmt

    @staticmethod
    def _deal_response(row, deal_team: list[dict] | None = None) -> DealResponse:
        deal = row[0]
        return DealResponse(
            id=deal.id,
            org_id=deal.org_id,
            team_id=deal.team_id,
            pipeline_id=deal.pipeline_id,
            pipeline_name=row.pipeline_name,
            stage_id=deal.stage_id,
            stage_name=row.stage_name,
            name=deal.name,
            value=float(deal.value),
            currency=deal.currency,
            probability=float(deal.probability),
            expected_close_date=deal.expected_close_date,
            actual_close_date=deal.actual_close_date,
            status=deal.status,
            owner_id=deal.owner_id,
            owner_name=row.owner_name,
            contact_id=deal.contact_id,
            contact_name=row.contact_name,
            company_id=deal.company_id,
            company_name=row.company_name,
            ai_score=float(deal.ai_score) if deal.ai_score is not None else None,
            ai_next_action=deal.ai_next_action,
            tags=list(deal.tags or []),
            custom_fields=dict(deal.custom_fields or {}),
            is_private=deal.is_private,
            is_rotting=bool(row.is_rotting),
            days_in_stage=int(row.days_in_stage or 0),
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            # PE identity fields
            description=deal.description,
            new_deal_date=deal.new_deal_date,
            transaction_type_id=str(deal.transaction_type_id) if deal.transaction_type_id else None,
            transaction_type_label=row.transaction_type_label,
            fund_id=str(deal.fund_id) if deal.fund_id else None,
            fund_name=row.fund_name,
            platform_or_addon=deal.platform_or_addon,
            platform_company_id=str(deal.platform_company_id) if deal.platform_company_id else None,
            platform_company_name=row.platform_company_name,
            # PE source tracking fields
            source_type_id=str(deal.source_type_id) if deal.source_type_id else None,
            source_type_label=row.source_type_label,
            source_company_id=str(deal.source_company_id) if deal.source_company_id else None,
            source_company_name=row.source_company_name,
            source_individual_id=str(deal.source_individual_id) if deal.source_individual_id else None,
            source_individual_name=row.source_individual_name if row.source_individual_name and row.source_individual_name.strip() else None,
            originator_id=str(deal.originator_id) if deal.originator_id else None,
            originator_name=row.originator_name,
            # PE financial fields
            revenue_amount=float(deal.revenue_amount) if deal.revenue_amount is not None else None,
            revenue_currency=deal.revenue_currency,
            ebitda_amount=float(deal.ebitda_amount) if deal.ebitda_amount is not None else None,
            ebitda_currency=deal.ebitda_currency,
            enterprise_value_amount=float(deal.enterprise_value_amount) if deal.enterprise_value_amount is not None else None,
            enterprise_value_currency=deal.enterprise_value_currency,
            equity_investment_amount=float(deal.equity_investment_amount) if deal.equity_investment_amount is not None else None,
            equity_investment_currency=deal.equity_investment_currency,
            loi_bid_amount=float(deal.loi_bid_amount) if deal.loi_bid_amount is not None else None,
            loi_bid_currency=deal.loi_bid_currency,
            ioi_bid_amount=float(deal.ioi_bid_amount) if deal.ioi_bid_amount is not None else None,
            ioi_bid_currency=deal.ioi_bid_currency,
            # PE date milestone fields
            cim_received_date=deal.cim_received_date,
            ioi_due_date=deal.ioi_due_date,
            ioi_submitted_date=deal.ioi_submitted_date,
            management_presentation_date=deal.management_presentation_date,
            loi_due_date=deal.loi_due_date,
            loi_submitted_date=deal.loi_submitted_date,
            live_diligence_date=deal.live_diligence_date,
            portfolio_company_date=deal.portfolio_company_date,
            # PE passed/dead fields
            passed_dead_date=deal.passed_dead_date,
            passed_dead_reasons=list(deal.passed_dead_reasons or []),
            passed_dead_commentary=deal.passed_dead_commentary,
            # Legacy
            legacy_id=deal.legacy_id,
            # Deal team (loaded separately for detail, empty for list)
            deal_team=deal_team if deal_team is not None else [],
        )

    async def _load_deal_team(self, deal_id: UUID) -> list[dict]:
        stmt = (
            select(User.id, User.full_name, User.email)
            .join(DealTeamMember, DealTeamMember.user_id == User.id)
            .where(DealTeamMember.deal_id == str(deal_id))
        )
        rows = (await self.db.execute(stmt)).all()
        return [{"id": str(row.id), "name": row.full_name or row.email} for row in rows]

    async def _set_deal_team(self, deal_id: UUID, user_ids: list[str]) -> None:
        from sqlalchemy import delete
        await self.db.execute(
            delete(DealTeamMember).where(DealTeamMember.deal_id == str(deal_id))
        )
        for uid in user_ids:
            self.db.add(DealTeamMember(deal_id=str(deal_id), user_id=str(uid)))
        await self.db.flush()

    @staticmethod
    def _activity_response(row) -> ActivityResponse:
        activity = row[0]
        return ActivityResponse(
            id=activity.id,
            deal_id=activity.deal_id,
            user_id=activity.user_id,
            user_name=row.user_name,
            activity_type=activity.activity_type,
            title=activity.title,
            body=activity.body,
            is_private=activity.is_private,
            occurred_at=activity.occurred_at,
            created_at=activity.created_at,
        )

    async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
        visible_team_ids = await self._visible_team_ids()
        stmt = select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id)
        if visible_team_ids is not None:
            if not visible_team_ids:
                stmt = stmt.where(False)
            else:
                stmt = stmt.where(Deal.team_id.in_(visible_team_ids))
        stmt = stmt.where(private_deal_predicate(self.current_user, visible_team_ids))
        deal = await self.db.scalar(stmt)
        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        return deal

    async def _get_pipeline_and_stage(self, pipeline_id: UUID, stage_id: UUID) -> tuple[Pipeline, PipelineStage]:
        pipeline = await self.db.scalar(
            select(Pipeline).where(
                Pipeline.id == pipeline_id,
                Pipeline.org_id == self.current_user.org_id,
                Pipeline.is_archived.is_(False),
            )
        )
        if pipeline is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pipeline not found")
        if pipeline.team_id is not None:
            visible_team_ids = await self._visible_team_ids()
            if not is_admin(self.current_user) and (
                visible_team_ids is None or pipeline.team_id not in visible_team_ids
            ):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        stage = await self.db.scalar(
            select(PipelineStage).where(PipelineStage.id == stage_id, PipelineStage.pipeline_id == pipeline.id)
        )
        if stage is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stage not found in pipeline")
        return pipeline, stage

    async def list_deals(
        self,
        pipeline_id: UUID | None = None,
        stage_id: UUID | None = None,
        owner_id: UUID | None = None,
        team_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        size: int = 25,
    ) -> DealListResponse:
        page, size = clamp_pagination(page, size)
        visible_team_ids = await self._visible_team_ids()
        stmt = self._base_deal_stmt(visible_team_ids)
        if pipeline_id is not None:
            stmt = stmt.where(Deal.pipeline_id == pipeline_id)
        if stage_id is not None:
            stmt = stmt.where(Deal.stage_id == stage_id)
        if owner_id is not None:
            stmt = stmt.where(Deal.owner_id == owner_id)
        if team_id is not None:
            stmt = stmt.where(Deal.team_id == team_id)
        if status is not None:
            stmt = stmt.where(Deal.status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Deal.name.ilike(term),
                    Contact.first_name.ilike(term),
                    Contact.last_name.ilike(term),
                    Company.name.ilike(term),
                )
            )
        stmt = apply_tag_filter(stmt, Deal.tags, tags)
        total = await count_rows(self.db, stmt)
        rows = (
            await self.db.execute(
                stmt.order_by(Deal.created_at.desc()).offset((page - 1) * size).limit(size)
            )
        ).all()
        return DealListResponse(
            items=[self._deal_response(row) for row in rows],
            total=total,
            page=page,
            size=size,
            pages=page_count(total, size),
        )

    async def get_deal(self, deal_id: UUID) -> DealResponse:
        visible_team_ids = await self._visible_team_ids()
        stmt = self._base_deal_stmt(visible_team_ids).where(Deal.id == deal_id)
        row = (await self.db.execute(stmt)).first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        deal_team = await self._load_deal_team(deal_id)
        return self._deal_response(row, deal_team=deal_team)

    async def create_deal(self, data: DealCreate) -> DealResponse:
        if self.current_user.team_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is not assigned to a team")
        if data.contact_id is not None:
            await ensure_contact_in_org(self.db, data.contact_id, self.current_user.org_id)
        if data.company_id is not None:
            await ensure_company_in_org(self.db, data.company_id, self.current_user.org_id)
        pipeline, stage = await self._get_pipeline_and_stage(data.pipeline_id, data.stage_id)
        if pipeline.team_id is not None and pipeline.team_id != self.current_user.team_id and not is_manager_plus(self.current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        status_value = "open"
        actual_close_date = None
        if stage.stage_type == "won":
            status_value = "won"
            actual_close_date = date.today()
        elif stage.stage_type == "lost":
            status_value = "lost"
            actual_close_date = date.today()

        deal = Deal(
            org_id=self.current_user.org_id,
            team_id=self.current_user.team_id,
            pipeline_id=pipeline.id,
            stage_id=stage.id,
            name=data.name,
            value=data.value,
            currency=data.currency,
            probability=data.probability if data.probability is not None else stage.probability,
            expected_close_date=data.expected_close_date,
            actual_close_date=actual_close_date,
            status=status_value,
            owner_id=self.current_user.id,
            contact_id=data.contact_id,
            company_id=data.company_id,
            tags=data.tags,
            is_private=data.is_private,
            custom_fields=data.custom_fields,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        self.db.add(deal)
        await self.db.flush()
        self.db.add(
            DealActivity(
                deal_id=deal.id,
                user_id=self.current_user.id,
                activity_type="deal_created",
                title="Deal created",
                occurred_at=utcnow(),
            )
        )
        await self.db.commit()
        return await self.get_deal(deal.id)

    async def update_deal(self, deal_id: UUID, data: DealUpdate) -> DealResponse:
        deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if data.owner_id is not None and not is_manager_plus(self.current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if data.contact_id is not None:
            await ensure_contact_in_org(self.db, data.contact_id, self.current_user.org_id)
        if data.company_id is not None:
            await ensure_company_in_org(self.db, data.company_id, self.current_user.org_id)

        # Core fields
        for field in ["name", "value", "currency", "probability", "expected_close_date", "actual_close_date", "status", "contact_id", "company_id", "is_private"]:
            value = getattr(data, field)
            if value is not None:
                setattr(deal, field, value)
        if data.owner_id is not None:
            owner = await self.db.scalar(select(User).where(User.id == data.owner_id, User.org_id == self.current_user.org_id))
            if owner is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner not found")
            if owner.team_id != deal.team_id and not is_admin(self.current_user):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner must belong to deal team")
            deal.owner_id = owner.id
        if data.tags is not None:
            deal.tags = data.tags
        if data.custom_fields is not None:
            deal.custom_fields = merge_custom_fields(deal.custom_fields, data.custom_fields)
        # PE scalar fields — apply all set (non-None) values
        pe_scalar_fields = [
            "description", "new_deal_date", "transaction_type_id", "fund_id",
            "platform_or_addon", "platform_company_id",
            "source_type_id", "source_company_id", "source_individual_id", "originator_id",
            "revenue_amount", "revenue_currency",
            "ebitda_amount", "ebitda_currency",
            "enterprise_value_amount", "enterprise_value_currency",
            "equity_investment_amount", "equity_investment_currency",
            "loi_bid_amount", "loi_bid_currency",
            "ioi_bid_amount", "ioi_bid_currency",
            "cim_received_date", "ioi_due_date", "ioi_submitted_date", "management_presentation_date",
            "loi_due_date", "loi_submitted_date", "live_diligence_date", "portfolio_company_date",
            "passed_dead_date", "passed_dead_commentary", "legacy_id",
        ]
        for field in pe_scalar_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(deal, field, value)
        # passed_dead_reasons is a list — use explicit check so empty list can clear it
        if data.passed_dead_reasons is not None:
            deal.passed_dead_reasons = data.passed_dead_reasons
        # Deal team — set if provided
        if data.deal_team_ids is not None:
            await self._set_deal_team(deal.id, data.deal_team_ids)
        deal.updated_by = self.current_user.id
        await self.db.commit()
        return await self.get_deal(deal.id)

    async def move_stage(self, deal_id: UUID, data: DealMoveStage) -> DealResponse:
        deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        old_stage = await self.db.scalar(select(PipelineStage).where(PipelineStage.id == deal.stage_id))
        new_stage = await self.db.scalar(
            select(PipelineStage).where(PipelineStage.id == data.stage_id, PipelineStage.pipeline_id == deal.pipeline_id)
        )
        if new_stage is None or old_stage is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stage not found")

        deal.stage_id = new_stage.id
        pipeline = await self.db.scalar(select(Pipeline).where(Pipeline.id == deal.pipeline_id))
        if pipeline is not None and pipeline.probability_model != "manual":
            deal.probability = new_stage.probability
        if new_stage.stage_type == "won":
            deal.status = "won"
            deal.actual_close_date = date.today()
        elif new_stage.stage_type == "lost":
            deal.status = "lost"
            deal.actual_close_date = date.today()
        else:
            deal.status = "open"
            deal.actual_close_date = None
        if data.log_activity:
            self.db.add(
                DealActivity(
                    deal_id=deal.id,
                    user_id=self.current_user.id,
                    activity_type="stage_change",
                    title=f"Moved from {old_stage.name} to {new_stage.name}",
                    occurred_at=utcnow(),
                )
            )
        await self.db.commit()
        return await self.get_deal(deal.id)

    async def get_deal_activities(
        self,
        deal_id: UUID,
        page: int = 1,
        size: int = 25,
    ) -> ActivityListResponse:
        deal = await self._get_deal_or_404(deal_id)
        page, size = clamp_pagination(page, size)
        stmt = (
            select(DealActivity, user_name_expr().label("user_name"))
            .join(User, User.id == DealActivity.user_id)
            .where(
                DealActivity.deal_id == deal.id,
                or_(DealActivity.is_private.is_(False), DealActivity.user_id == self.current_user.id),
            )
        )
        total = await count_rows(self.db, stmt)
        rows = (
            await self.db.execute(
                stmt.order_by(DealActivity.occurred_at.desc()).offset((page - 1) * size).limit(size)
            )
        ).all()
        return ActivityListResponse(
            items=[self._activity_response(row) for row in rows],
            total=total,
            page=page,
            size=size,
            pages=page_count(total, size),
        )

    async def log_activity(self, deal_id: UUID, data: ActivityCreate) -> ActivityResponse:
        deal = await self._get_deal_or_404(deal_id)
        activity = DealActivity(
            deal_id=deal.id,
            user_id=self.current_user.id,
            activity_type=data.activity_type,
            title=data.title,
            body=data.body,
            is_private=data.is_private,
            occurred_at=data.occurred_at or utcnow(),
        )
        self.db.add(activity)
        await self.db.commit()
        row = (
            await self.db.execute(
                select(DealActivity, user_name_expr().label("user_name"))
                .join(User, User.id == DealActivity.user_id)
                .where(DealActivity.id == activity.id)
            )
        ).first()
        return self._activity_response(row)

    async def delete_deal(self, deal_id: UUID) -> None:
        deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if not (is_admin(self.current_user) or deal.owner_id == self.current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        await self.db.delete(deal)
        await self.db.commit()
