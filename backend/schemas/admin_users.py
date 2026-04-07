from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminUserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="regular_user")
    team_id: Optional[UUID] = None


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    team_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: UUID
    full_name: Optional[str]
    email: str
    role: str
    team_id: Optional[UUID]
    group_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
