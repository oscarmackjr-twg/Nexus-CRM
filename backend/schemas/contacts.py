from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.schemas.deals import ActivityResponse


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    title: str | None = None
    company_id: UUID | None = None
    lifecycle_stage: str = "lead"
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict = Field(default_factory=dict)
    # PE Blueprint fields
    business_phone: str | None = None
    mobile_phone: str | None = None
    assistant_name: str | None = None
    assistant_email: str | None = None
    assistant_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    contact_type_id: str | None = None
    primary_contact: bool | None = None
    contact_frequency: int | None = None
    sector: list[str] | None = None
    sub_sector: list[str] | None = None
    previous_employment: list[dict] | None = None
    board_memberships: list[dict] | None = None
    linkedin_url: str | None = None
    legacy_id: str | None = None
    coverage_persons: list[str] | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    title: str | None = None
    company_id: UUID | None = None
    owner_id: UUID | None = None
    lead_score: int | None = None
    lifecycle_stage: str | None = None
    tags: list[str] | None = None
    custom_fields: dict | None = None
    # PE Blueprint fields
    business_phone: str | None = None
    mobile_phone: str | None = None
    assistant_name: str | None = None
    assistant_email: str | None = None
    assistant_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    contact_type_id: str | None = None
    primary_contact: bool | None = None
    contact_frequency: int | None = None
    sector: list[str] | None = None
    sub_sector: list[str] | None = None
    previous_employment: list[dict] | None = None
    board_memberships: list[dict] | None = None
    linkedin_url: str | None = None
    legacy_id: str | None = None
    coverage_persons: list[str] | None = None


class ContactActivityCreate(BaseModel):
    activity_type: str
    notes: str | None = None
    occurred_at: datetime
    deal_id: UUID | None = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    company_id: UUID | None = None
    company_name: str | None = None
    linkedin_profile_url: str | None = None
    linkedin_member_id: str | None = None
    linkedin_synced_at: datetime | None = None
    owner_id: UUID | None = None
    owner_name: str | None = None
    lead_score: int
    lifecycle_stage: str
    tags: list[str]
    custom_fields: dict = Field(default_factory=dict)
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    # PE Blueprint fields
    business_phone: str | None = None
    mobile_phone: str | None = None
    assistant_name: str | None = None
    assistant_email: str | None = None
    assistant_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    contact_type_id: str | None = None
    contact_type_label: str | None = None
    primary_contact: bool | None = None
    contact_frequency: int | None = None
    sector: list[str] = Field(default_factory=list)
    sub_sector: list[str] = Field(default_factory=list)
    previous_employment: list[dict] = Field(default_factory=list)
    board_memberships: list[dict] = Field(default_factory=list)
    linkedin_url: str | None = None
    legacy_id: str | None = None
    coverage_persons: list[dict] = Field(default_factory=list)
    related_deal_count: int | None = None
    recent_activity: list[ActivityResponse] | None = None


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    size: int
    pages: int
