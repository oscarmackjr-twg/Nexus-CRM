from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FundCreate(BaseModel):
    fund_name: str
    fundraise_status_id: str | None = None
    target_fund_size_amount: float | None = None
    target_fund_size_currency: str | None = None
    vintage_year: int | None = None


class FundUpdate(BaseModel):
    fund_name: str | None = None
    fundraise_status_id: str | None = None
    target_fund_size_amount: float | None = None
    target_fund_size_currency: str | None = None
    vintage_year: int | None = None


class FundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    fund_name: str
    fundraise_status_id: str | None = None
    fundraise_status_label: str | None = None
    target_fund_size_amount: float | None = None
    target_fund_size_currency: str | None = None
    vintage_year: int | None = None
    created_at: datetime
