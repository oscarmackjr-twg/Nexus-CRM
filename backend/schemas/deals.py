from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.pipelines import PipelineResponse, StageResponse


class DealCreate(BaseModel):
    name: str
    pipeline_id: UUID
    stage_id: UUID
    value: float = 0
    currency: str = "USD"
    probability: float | None = None
    expected_close_date: date | None = None
    contact_id: UUID | None = None
    company_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    is_private: bool = False
    custom_fields: dict = Field(default_factory=dict)
    # Deal team (DEAL-02) — initial team assignment
    deal_team_ids: list[str] | None = None


class DealUpdate(BaseModel):
    name: str | None = None
    value: float | None = None
    currency: str | None = None
    probability: float | None = None
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    status: str | None = None
    owner_id: UUID | None = None
    contact_id: UUID | None = None
    company_id: UUID | None = None
    tags: list[str] | None = None
    is_private: bool | None = None
    custom_fields: dict | None = None
    # Identity (DEAL-01, DEAL-03)
    description: str | None = None
    new_deal_date: date | None = None
    transaction_type_id: str | None = None
    fund_id: str | None = None
    platform_or_addon: str | None = None
    platform_company_id: str | None = None
    # Source tracking (DEAL-04)
    source_type_id: str | None = None
    source_company_id: str | None = None
    source_individual_id: str | None = None
    originator_id: str | None = None
    # Financials (DEAL-05)
    revenue_amount: float | None = None
    revenue_currency: str | None = None
    ebitda_amount: float | None = None
    ebitda_currency: str | None = None
    enterprise_value_amount: float | None = None
    enterprise_value_currency: str | None = None
    equity_investment_amount: float | None = None
    equity_investment_currency: str | None = None
    # Bids (DEAL-06)
    loi_bid_amount: float | None = None
    loi_bid_currency: str | None = None
    ioi_bid_amount: float | None = None
    ioi_bid_currency: str | None = None
    # Date milestones (DEAL-07)
    cim_received_date: date | None = None
    ioi_due_date: date | None = None
    ioi_submitted_date: date | None = None
    management_presentation_date: date | None = None
    loi_due_date: date | None = None
    loi_submitted_date: date | None = None
    live_diligence_date: date | None = None
    portfolio_company_date: date | None = None
    # Passed/dead (DEAL-08)
    passed_dead_date: date | None = None
    passed_dead_reasons: list[str] | None = None
    passed_dead_commentary: str | None = None
    # Legacy (DEAL-09)
    legacy_id: str | None = None
    # Deal team (DEAL-02) — handled in service, not an ORM column
    deal_team_ids: list[str] | None = None


class DealMoveStage(BaseModel):
    stage_id: UUID
    log_activity: bool = True


class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    team_id: UUID
    pipeline_id: UUID
    pipeline_name: str
    stage_id: UUID
    stage_name: str
    name: str
    value: float
    currency: str
    probability: float
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    status: str
    owner_id: UUID
    owner_name: str
    contact_id: UUID | None = None
    contact_name: str | None = None
    company_id: UUID | None = None
    company_name: str | None = None
    ai_score: float | None = None
    ai_next_action: str | None = None
    tags: list[str]
    custom_fields: dict = Field(default_factory=dict)
    is_private: bool
    is_rotting: bool
    days_in_stage: int
    created_at: datetime
    updated_at: datetime
    # Identity (DEAL-01, DEAL-03)
    description: str | None = None
    new_deal_date: date | None = None
    transaction_type_id: str | None = None
    transaction_type_label: str | None = None
    fund_id: str | None = None
    fund_name: str | None = None
    platform_or_addon: str | None = None
    platform_company_id: str | None = None
    platform_company_name: str | None = None
    # Source tracking (DEAL-04)
    source_type_id: str | None = None
    source_type_label: str | None = None
    source_company_id: str | None = None
    source_company_name: str | None = None
    source_individual_id: str | None = None
    source_individual_name: str | None = None
    originator_id: str | None = None
    originator_name: str | None = None
    # Financials (DEAL-05)
    revenue_amount: float | None = None
    revenue_currency: str | None = None
    ebitda_amount: float | None = None
    ebitda_currency: str | None = None
    enterprise_value_amount: float | None = None
    enterprise_value_currency: str | None = None
    equity_investment_amount: float | None = None
    equity_investment_currency: str | None = None
    # Bids (DEAL-06)
    loi_bid_amount: float | None = None
    loi_bid_currency: str | None = None
    ioi_bid_amount: float | None = None
    ioi_bid_currency: str | None = None
    # Date milestones (DEAL-07)
    cim_received_date: date | None = None
    ioi_due_date: date | None = None
    ioi_submitted_date: date | None = None
    management_presentation_date: date | None = None
    loi_due_date: date | None = None
    loi_submitted_date: date | None = None
    live_diligence_date: date | None = None
    portfolio_company_date: date | None = None
    # Passed/dead (DEAL-08)
    passed_dead_date: date | None = None
    passed_dead_reasons: list[str] = Field(default_factory=list)
    passed_dead_commentary: str | None = None
    # Legacy (DEAL-09)
    legacy_id: str | None = None
    # Deal team (DEAL-02, D-17)
    deal_team: list[dict] = Field(default_factory=list)


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    page: int
    size: int
    pages: int


class ActivityCreate(BaseModel):
    activity_type: str
    title: str | None = None
    body: str | None = None
    is_private: bool = False
    occurred_at: datetime | None = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    user_id: UUID
    user_name: str
    activity_type: str
    title: str | None = None
    body: str | None = None
    is_private: bool
    occurred_at: datetime
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    size: int
    pages: int


class KanbanColumn(BaseModel):
    stage: StageResponse
    deals: list[DealResponse]
    aggregate_value: float


class PipelineKanbanResponse(BaseModel):
    pipeline: PipelineResponse
    columns: list[KanbanColumn]
