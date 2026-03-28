from __future__ import annotations

import math
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DealFundingCreate(BaseModel):
    capital_provider_id: UUID | None = None
    status_id: UUID | None = None
    projected_commitment_amount: float | None = None
    projected_commitment_currency: str | None = None
    actual_commitment_amount: float | None = None
    actual_commitment_currency: str | None = None
    actual_commitment_date: date | None = None
    terms: str | None = None
    comments_next_steps: str | None = None


class DealFundingUpdate(BaseModel):
    capital_provider_id: UUID | None = None
    status_id: UUID | None = None
    projected_commitment_amount: float | None = None
    projected_commitment_currency: str | None = None
    actual_commitment_amount: float | None = None
    actual_commitment_currency: str | None = None
    actual_commitment_date: date | None = None
    terms: str | None = None
    comments_next_steps: str | None = None


class DealFundingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    deal_id: UUID
    capital_provider_id: UUID | None = None
    capital_provider_name: str | None = None    # resolved via JOIN
    status_id: UUID | None = None
    status_label: str | None = None             # resolved via JOIN
    projected_commitment_amount: float | None = None
    projected_commitment_currency: str | None = None
    actual_commitment_amount: float | None = None
    actual_commitment_currency: str | None = None
    actual_commitment_date: date | None = None
    terms: str | None = None
    comments_next_steps: str | None = None
    created_at: datetime
    updated_at: datetime


class DealFundingListResponse(BaseModel):
    items: list[DealFundingResponse]
    total: int
    page: int
    size: int
    pages: int
