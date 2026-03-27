from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RefDataCreate(BaseModel):
    category: str
    value: str
    label: str
    position: int = 0


class RefDataUpdate(BaseModel):
    label: str | None = None
    position: int | None = None
    is_active: bool | None = None


class RefDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID | None
    category: str
    value: str
    label: str
    position: int
    is_active: bool
    created_at: datetime
