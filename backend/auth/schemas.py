from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserRole(str, Enum):
    admin = "admin"
    supervisor = "supervisor"
    principal = "principal"
    regular_user = "regular_user"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    org_name: Optional[str] = None
    org_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    role: UserRole = UserRole.regular_user


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    org_id: UUID
    team_id: Optional[UUID] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    team_id: Optional[UUID] = None
    is_active: Optional[bool] = None
