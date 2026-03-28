from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

JSONVariant = JSON().with_variant(JSONB, "postgresql")
StringList = MutableList.as_mutable(JSON()).with_variant(ARRAY(Text()), "postgresql")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free", server_default="free")
    linkedin_org_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    teams: Mapped[list[Team]] = relationship(back_populates="org", cascade="all, delete-orphan")
    users: Mapped[list[User]] = relationship(back_populates="org", cascade="all, delete-orphan")
    contacts: Mapped[list[Contact]] = relationship(back_populates="org", cascade="all, delete-orphan")
    companies: Mapped[list[Company]] = relationship(back_populates="org", cascade="all, delete-orphan")
    pipelines: Mapped[list[Pipeline]] = relationship(back_populates="org", cascade="all, delete-orphan")
    deals: Mapped[list[Deal]] = relationship(back_populates="org", cascade="all, delete-orphan")
    boards: Mapped[list[Board]] = relationship(back_populates="org", cascade="all, delete-orphan")
    pages: Mapped[list[Page]] = relationship(back_populates="org", cascade="all, delete-orphan")
    automations: Mapped[list[Automation]] = relationship(back_populates="org", cascade="all, delete-orphan")
    ai_queries: Mapped[list[AIQuery]] = relationship(back_populates="org", cascade="all, delete-orphan")
    funds: Mapped[list["Fund"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        Index("ix_teams_org_parent", "org_id", "parent_team_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="sales", server_default="sales")
    settings: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Organization] = relationship(back_populates="teams")
    parent_team: Mapped[Optional[Team]] = relationship(remote_side=[id], back_populates="sub_teams")
    sub_teams: Mapped[list[Team]] = relationship(back_populates="parent_team")
    members: Mapped[list[User]] = relationship(back_populates="team")
    pipelines: Mapped[list[Pipeline]] = relationship(back_populates="team")
    deals: Mapped[list[Deal]] = relationship(back_populates="team")
    boards: Mapped[list[Board]] = relationship(back_populates="team")
    pages: Mapped[list[Page]] = relationship(back_populates="team")
    automations: Mapped[list[Automation]] = relationship(back_populates="team")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_org_role", "org_id", "role"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="rep", server_default="rep")
    team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    linkedin_member_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Organization] = relationship(back_populates="users")
    team: Mapped[Optional[Team]] = relationship(back_populates="members")
    owned_contacts: Mapped[list[Contact]] = relationship(back_populates="owner", foreign_keys="Contact.owner_id")
    owned_companies: Mapped[list[Company]] = relationship(back_populates="owner", foreign_keys="Company.owner_id")
    owned_deals: Mapped[list[Deal]] = relationship(back_populates="owner", foreign_keys="Deal.owner_id")
    created_pipelines: Mapped[list[Pipeline]] = relationship(back_populates="creator", foreign_keys="Pipeline.created_by")
    created_boards: Mapped[list[Board]] = relationship(back_populates="creator", foreign_keys="Board.created_by")
    created_pages: Mapped[list[Page]] = relationship(back_populates="creator", foreign_keys="Page.created_by")
    edited_pages: Mapped[list[Page]] = relationship(back_populates="last_editor", foreign_keys="Page.last_edited_by")
    assigned_tasks: Mapped[list[Task]] = relationship(back_populates="assignee", foreign_keys="Task.assignee_id")
    created_tasks: Mapped[list[Task]] = relationship(back_populates="creator", foreign_keys="Task.created_by")
    created_automations: Mapped[list[Automation]] = relationship(back_populates="creator", foreign_keys="Automation.created_by")
    activities: Mapped[list[DealActivity]] = relationship(back_populates="user")
    ai_queries: Mapped[list[AIQuery]] = relationship(back_populates="user")


class ContactCoveragePerson(Base):
    __tablename__ = "contact_coverage_persons"
    contact_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_org_lifecycle", "org_id", "lifecycle_stage"),
        Index("ix_contacts_org_archived", "org_id", "is_archived"),
        UniqueConstraint("org_id", "legacy_id", name="uq_contacts_org_legacy_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    linkedin_profile_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_member_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    lifecycle_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="lead", server_default="lead")
    tags: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # PE Blueprint fields (Phase 3)
    business_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assistant_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assistant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assistant_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_type_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True)
    primary_contact: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contact_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sector: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    sub_sector: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    previous_employment: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    board_memberships: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    org: Mapped[Organization] = relationship(back_populates="contacts")
    company: Mapped[Optional[Company]] = relationship(back_populates="contacts")
    owner: Mapped[Optional[User]] = relationship(back_populates="owned_contacts", foreign_keys=[owner_id])
    deals: Mapped[list[Deal]] = relationship(back_populates="contact", foreign_keys="Deal.contact_id")
    coverage_persons: Mapped[list["User"]] = relationship(
        "User",
        secondary="contact_coverage_persons",
        lazy="selectin",
    )


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_org_name", "org_id", "name"),
        UniqueConstraint("org_id", "legacy_id", name="uq_companies_org_legacy_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_range: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_company_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # PE Blueprint fields (Phase 3) — COMPANY-01 through COMPANY-09
    # COMPANY-01: Identity fields
    company_type_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True)
    company_sub_type_ids: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # COMPANY-02: Phone + parent
    main_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    parent_company_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    # COMPANY-03: Address fields (country not in original model)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # COMPANY-04: Ref_data FK fields
    tier_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True)
    sector_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True)
    sub_sector_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True, index=True)
    # COMPANY-05: Investment preference fields
    sector_preferences: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    sub_sector_preferences: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    preference_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # COMPANY-06: Financial fields
    aum_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    aum_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    ebitda_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    ebitda_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    # COMPANY-07: Bite size + co-invest
    typical_bite_size_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    typical_bite_size_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    bite_size_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    co_invest: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    target_deal_size_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    # COMPANY-08: Deal preference fields
    transaction_types: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    min_ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    max_ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    ebitda_range_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    # COMPANY-09: Relationship fields
    watchlist: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    coverage_person_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    contact_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    org: Mapped[Organization] = relationship(back_populates="companies")
    owner: Mapped[Optional[User]] = relationship(back_populates="owned_companies", foreign_keys=[owner_id])
    contacts: Mapped[list[Contact]] = relationship(back_populates="company")
    deals: Mapped[list[Deal]] = relationship(back_populates="company", foreign_keys="Deal.company_id")
    parent_company: Mapped[Optional["Company"]] = relationship(
        "Company", remote_side="Company.id", foreign_keys=[parent_company_id]
    )


class Pipeline(Base):
    __tablename__ = "pipelines"
    __table_args__ = (
        Index("ix_pipelines_org_default", "org_id", "is_default"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    probability_model: Mapped[str] = mapped_column(String(20), nullable=False, default="manual", server_default="manual")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Organization] = relationship(back_populates="pipelines")
    team: Mapped[Optional[Team]] = relationship(back_populates="pipelines")
    creator: Mapped[User] = relationship(back_populates="created_pipelines", foreign_keys=[created_by])
    stages: Mapped[list[PipelineStage]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")
    deals: Mapped[list[Deal]] = relationship(back_populates="pipeline")
    boards: Mapped[list[Board]] = relationship(back_populates="linked_pipeline")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "position", name="uq_pipeline_stage_position"),
        Index("ix_pipeline_stages_pipeline_position", "pipeline_id", "position"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    pipeline_id: Mapped[UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    stage_type: Mapped[str] = mapped_column(String(10), nullable=False, default="open", server_default="open")
    rotting_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pipeline: Mapped[Pipeline] = relationship(back_populates="stages")
    deals: Mapped[list[Deal]] = relationship(back_populates="stage")


class Fund(Base):
    __tablename__ = "funds"
    __table_args__ = (
        Index("ix_funds_org_id", "org_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fundraise_status_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    target_fund_size_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    target_fund_size_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    vintage_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Organization] = relationship(back_populates="funds")
    deals: Mapped[list["Deal"]] = relationship(back_populates="fund")


class DealTeamMember(Base):
    __tablename__ = "deal_team_members"
    deal_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_org_team", "org_id", "team_id"),
        Index("ix_deals_pipeline_stage", "pipeline_id", "stage_id"),
        Index("ix_deals_org_status", "org_id", "status"),
        UniqueConstraint("org_id", "legacy_id", name="uq_deals_org_legacy_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    pipeline_id: Mapped[UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="RESTRICT"), nullable=False)
    stage_id: Mapped[UUID] = mapped_column(ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", server_default="open")
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    contact_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    fund_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("funds.id", ondelete="SET NULL"), nullable=True, index=True)
    ai_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    ai_score_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_next_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # PE Blueprint fields (Phase 4) — DEAL-01 through DEAL-09
    # DEAL-01: Identity fields
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_deal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    transaction_type_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    platform_or_addon: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    platform_company_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    # DEAL-04: Source tracking fields
    source_type_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("ref_data.id", ondelete="SET NULL"), nullable=True)
    source_company_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    source_individual_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    originator_id: Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # DEAL-05: Financial fields (amount + currency pairs)
    revenue_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    revenue_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    ebitda_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    ebitda_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    enterprise_value_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    enterprise_value_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    equity_investment_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    equity_investment_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    # DEAL-06: Bid fields
    loi_bid_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    loi_bid_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    ioi_bid_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    ioi_bid_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    # DEAL-07: Date milestone fields
    cim_received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ioi_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ioi_submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    management_presentation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    loi_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    loi_submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    live_diligence_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    portfolio_company_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # DEAL-08: Passed/dead fields
    passed_dead_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    passed_dead_reasons: Mapped[Optional[list]] = mapped_column(JSONVariant, nullable=True)
    passed_dead_commentary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # DEAL-09: Legacy ID (org-scoped unique constraint in __table_args__)
    legacy_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    org: Mapped[Organization] = relationship(back_populates="deals")
    team: Mapped[Team] = relationship(back_populates="deals")
    pipeline: Mapped[Pipeline] = relationship(back_populates="deals")
    stage: Mapped[PipelineStage] = relationship(back_populates="deals")
    owner: Mapped[User] = relationship(back_populates="owned_deals", foreign_keys=[owner_id])
    contact: Mapped[Optional[Contact]] = relationship(back_populates="deals", foreign_keys=[contact_id])
    company: Mapped[Optional[Company]] = relationship(back_populates="deals", foreign_keys=[company_id])
    fund: Mapped[Optional["Fund"]] = relationship(back_populates="deals")
    activities: Mapped[list[DealActivity]] = relationship(back_populates="deal", cascade="all, delete-orphan")
    deal_team_members: Mapped[list["DealTeamMember"]] = relationship(cascade="all, delete-orphan")
    platform_company: Mapped[Optional["Company"]] = relationship(foreign_keys=[platform_company_id])
    source_company: Mapped[Optional["Company"]] = relationship(foreign_keys=[source_company_id])
    source_individual: Mapped[Optional["Contact"]] = relationship(foreign_keys=[source_individual_id])
    originator: Mapped[Optional["User"]] = relationship(foreign_keys=[originator_id])


class DealActivity(Base):
    __tablename__ = "deal_activities"
    __table_args__ = (
        Index("ix_deal_activities_deal_type", "deal_id", "activity_type"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    deal_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    linkedin_message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    deal: Mapped[Optional[Deal]] = relationship(back_populates="activities", foreign_keys=[deal_id])
    user: Mapped[User] = relationship(back_populates="activities")


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    board_type: Mapped[str] = mapped_column(String(20), nullable=False, default="tasks", server_default="tasks")
    linked_pipeline_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    org: Mapped[Organization] = relationship(back_populates="boards")
    team: Mapped[Optional[Team]] = relationship(back_populates="boards")
    linked_pipeline: Mapped[Optional[Pipeline]] = relationship(back_populates="boards")
    creator: Mapped[User] = relationship(back_populates="created_boards", foreign_keys=[created_by])
    columns: Mapped[list[BoardColumn]] = relationship(back_populates="board", cascade="all, delete-orphan")
    tasks: Mapped[list[Task]] = relationship(back_populates="board", cascade="all, delete-orphan")


class BoardColumn(Base):
    __tablename__ = "board_columns"
    __table_args__ = (
        UniqueConstraint("board_id", "position", name="uq_board_column_position"),
        Index("ix_board_columns_board_position", "board_id", "position"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    board: Mapped[Board] = relationship(back_populates="columns")
    tasks: Mapped[list[Task]] = relationship(back_populates="column")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_board_column", "board_id", "column_id"),
        Index("ix_tasks_assignee_due", "assignee_id", "due_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    column_id: Mapped[UUID] = mapped_column(ForeignKey("board_columns.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", server_default="todo")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="none", server_default="none")
    assignee_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deal_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    position: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False, default=0, server_default="0")
    tags: Mapped[list[str]] = mapped_column(StringList, nullable=False, default=list)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    board: Mapped[Board] = relationship(back_populates="tasks")
    column: Mapped[BoardColumn] = relationship(back_populates="tasks")
    assignee: Mapped[Optional[User]] = relationship(back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator: Mapped[User] = relationship(back_populates="created_tasks", foreign_keys=[created_by])
    deal: Mapped[Optional[Deal]] = relationship(foreign_keys=[deal_id])
    contact: Mapped[Optional[Contact]] = relationship(foreign_keys=[contact_id])


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (
        Index("ix_pages_org_parent", "org_id", "parent_page_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_page_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    last_edited_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    org: Mapped[Organization] = relationship(back_populates="pages")
    team: Mapped[Optional[Team]] = relationship(back_populates="pages")
    parent_page: Mapped[Optional[Page]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list[Page]] = relationship(back_populates="parent_page")
    creator: Mapped[User] = relationship(back_populates="created_pages", foreign_keys=[created_by])
    last_editor: Mapped[Optional[User]] = relationship(back_populates="edited_pages", foreign_keys=[last_edited_by])


class Automation(Base):
    __tablename__ = "automations"
    __table_args__ = (
        Index("ix_automations_org_enabled", "org_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_config: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    conditions: Mapped[list[dict]] = mapped_column(JSONVariant, nullable=False, default=list)
    actions: Mapped[list[dict]] = mapped_column(JSONVariant, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    org: Mapped[Organization] = relationship(back_populates="automations")
    team: Mapped[Optional[Team]] = relationship(back_populates="automations")
    creator: Mapped[User] = relationship(back_populates="created_automations", foreign_keys=[created_by])
    runs: Mapped[list[AutomationRun]] = relationship(back_populates="automation", cascade="all, delete-orphan")


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (
        Index("ix_automation_runs_automation_status", "automation_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    automation_id: Mapped[UUID] = mapped_column(ForeignKey("automations.id", ondelete="CASCADE"), nullable=False)
    trigger_payload: Mapped[dict] = mapped_column(JSONVariant, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    result: Mapped[Optional[dict]] = mapped_column(JSONVariant, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    automation: Mapped[Automation] = relationship(back_populates="runs")


class AIQuery(Base):
    __tablename__ = "ai_queries"
    __table_args__ = (
        Index("ix_ai_queries_org_created", "org_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success", server_default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    org: Mapped[Organization] = relationship(back_populates="ai_queries")
    user: Mapped[Optional[User]] = relationship(back_populates="ai_queries")


class RefData(Base):
    __tablename__ = "ref_data"
    __table_args__ = (
        UniqueConstraint("org_id", "category", "value", name="uq_ref_data_org_category_value"),
        Index("ix_ref_data_org_category", "org_id", "category"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    org_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
