from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    size_range: str | None = None
    annual_revenue: float | None = None
    website: str | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict = Field(default_factory=dict)
    # PE Blueprint fields (Phase 3)
    company_type_id: str | None = None
    company_sub_type_ids: list[str] | None = None
    description: str | None = None
    main_phone: str | None = None
    parent_company_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    tier_id: str | None = None
    sector_id: str | None = None
    sub_sector_id: str | None = None
    sector_preferences: list[str] | None = None
    sub_sector_preferences: list[str] | None = None
    preference_notes: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    ebitda_amount: float | None = None
    ebitda_currency: str | None = None
    typical_bite_size_low: float | None = None
    typical_bite_size_high: float | None = None
    bite_size_currency: str | None = None
    co_invest: bool | None = None
    target_deal_size_id: str | None = None
    transaction_types: list[str] | None = None
    min_ebitda: float | None = None
    max_ebitda: float | None = None
    ebitda_range_currency: str | None = None
    watchlist: bool | None = None
    coverage_person_id: str | None = None
    contact_frequency: int | None = None
    legacy_id: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    size_range: str | None = None
    annual_revenue: float | None = None
    website: str | None = None
    owner_id: UUID | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None
    # PE Blueprint fields (Phase 3)
    company_type_id: str | None = None
    company_sub_type_ids: list[str] | None = None
    description: str | None = None
    main_phone: str | None = None
    parent_company_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    tier_id: str | None = None
    sector_id: str | None = None
    sub_sector_id: str | None = None
    sector_preferences: list[str] | None = None
    sub_sector_preferences: list[str] | None = None
    preference_notes: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    ebitda_amount: float | None = None
    ebitda_currency: str | None = None
    typical_bite_size_low: float | None = None
    typical_bite_size_high: float | None = None
    bite_size_currency: str | None = None
    co_invest: bool | None = None
    target_deal_size_id: str | None = None
    transaction_types: list[str] | None = None
    min_ebitda: float | None = None
    max_ebitda: float | None = None
    ebitda_range_currency: str | None = None
    watchlist: bool | None = None
    coverage_person_id: str | None = None
    contact_frequency: int | None = None
    legacy_id: str | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    domain: str | None = None
    industry: str | None = None
    size_range: str | None = None
    annual_revenue: float | None = None
    website: str | None = None
    linkedin_company_id: str | None = None
    linkedin_synced_at: datetime | None = None
    owner_id: UUID | None = None
    owner_name: str | None = None
    tags: list[str]
    custom_fields: dict = Field(default_factory=dict)
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    # PE Blueprint fields (Phase 3)
    company_type_id: str | None = None
    company_type_label: str | None = None
    company_sub_type_ids: list[str] = Field(default_factory=list)
    description: str | None = None
    main_phone: str | None = None
    parent_company_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    tier_id: str | None = None
    tier_label: str | None = None
    sector_id: str | None = None
    sector_label: str | None = None
    sub_sector_id: str | None = None
    sub_sector_label: str | None = None
    sector_preferences: list[str] = Field(default_factory=list)
    sub_sector_preferences: list[str] = Field(default_factory=list)
    preference_notes: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    ebitda_amount: float | None = None
    ebitda_currency: str | None = None
    typical_bite_size_low: float | None = None
    typical_bite_size_high: float | None = None
    bite_size_currency: str | None = None
    co_invest: bool | None = None
    target_deal_size_id: str | None = None
    transaction_types: list[str] = Field(default_factory=list)
    min_ebitda: float | None = None
    max_ebitda: float | None = None
    ebitda_range_currency: str | None = None
    watchlist: bool | None = None
    coverage_person_id: str | None = None
    coverage_person_name: str | None = None
    contact_frequency: int | None = None
    legacy_id: str | None = None
    linked_contacts_count: int | None = None
    open_deals_count: int | None = None


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    page: int
    size: int
    pages: int
