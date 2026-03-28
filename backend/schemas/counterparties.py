from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DealCounterpartyCreate(BaseModel):
    company_id: UUID  # required per D-06
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    tier_id: UUID | None = None
    investor_type_id: UUID | None = None
    check_size_amount: float | None = None
    check_size_currency: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    next_steps: str | None = None
    notes: str | None = None
    position: int | None = None


class DealCounterpartyUpdate(BaseModel):
    company_id: UUID | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    nda_sent_at: date | None = None
    nda_signed_at: date | None = None
    nrl_signed_at: date | None = None
    intro_materials_sent_at: date | None = None
    vdr_access_granted_at: date | None = None
    feedback_received_at: date | None = None
    tier_id: UUID | None = None
    investor_type_id: UUID | None = None
    check_size_amount: float | None = None
    check_size_currency: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    next_steps: str | None = None
    notes: str | None = None
    position: int | None = None


class DealCounterpartyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    deal_id: UUID
    company_id: UUID | None = None
    company_name: str | None = None           # resolved via JOIN
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    nda_sent_at: date | None = None
    nda_signed_at: date | None = None
    nrl_signed_at: date | None = None
    intro_materials_sent_at: date | None = None
    vdr_access_granted_at: date | None = None
    feedback_received_at: date | None = None
    tier_id: UUID | None = None
    tier_label: str | None = None             # resolved via JOIN
    investor_type_id: UUID | None = None
    investor_type_label: str | None = None    # resolved via JOIN
    check_size_amount: float | None = None
    check_size_currency: str | None = None
    aum_amount: float | None = None
    aum_currency: str | None = None
    next_steps: str | None = None
    notes: str | None = None
    position: int | None = None
    created_at: datetime
    updated_at: datetime


class DealCounterpartyListResponse(BaseModel):
    items: list[DealCounterpartyResponse]
    total: int
    page: int
    size: int
    pages: int
