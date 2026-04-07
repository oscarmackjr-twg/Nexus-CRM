from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class GroupResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
