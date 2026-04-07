from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.dependencies import get_db, require_role
from backend.auth.security import hash_password
from backend.models import Team, User
from backend.schemas.admin_users import AdminUserCreate, AdminUserResponse, AdminUserUpdate

router = APIRouter(prefix="/admin/users", tags=["admin"])

VALID_ROLES = {"admin", "supervisor", "principal", "regular_user"}


def _user_response(user: User) -> AdminUserResponse:
    group_name = user.team.name if user.team else None
    return AdminUserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        team_id=user.team_id,
        group_name=group_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/", response_model=list[AdminUserResponse])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserResponse]:
    stmt = (
        select(User)
        .where(User.org_id == current_user.org_id)
        .options(selectinload(User.team))
        .order_by(User.created_at)
    )
    users = (await db.execute(stmt)).scalars().all()
    return [_user_response(u) for u in users]


@router.post("/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    # Validate role
    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {sorted(VALID_ROLES)}",
        )
    # Check email uniqueness
    existing = await db.scalar(select(User).where(User.email == str(payload.email)))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    # Generate unique username from email
    base_username = str(payload.email).split("@")[0]
    username = base_username
    suffix = 1
    while await db.scalar(select(User).where(User.username == username)) is not None:
        username = f"{base_username}{suffix}"
        suffix += 1

    # Validate team_id belongs to the org
    if payload.team_id is not None:
        team = await db.scalar(
            select(Team).where(Team.id == payload.team_id, Team.org_id == current_user.org_id)
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in org"
            )

    user = User(
        org_id=current_user.org_id,
        email=str(payload.email),
        username=username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        team_id=payload.team_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.commit()

    stmt = select(User).where(User.id == user.id).options(selectinload(User.team))
    refreshed = (await db.execute(stmt)).scalar_one()
    return _user_response(refreshed)


@router.patch("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    stmt = (
        select(User)
        .where(User.id == user_id, User.org_id == current_user.org_id)
        .options(selectinload(User.team))
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {sorted(VALID_ROLES)}",
            )
        user.role = payload.role

    if payload.team_id is not None:
        # Validate team belongs to org
        team = await db.scalar(
            select(Team).where(Team.id == payload.team_id, Team.org_id == current_user.org_id)
        )
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in org"
            )
        user.team_id = payload.team_id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.flush()
    await db.commit()

    # Re-query with team loaded to get fresh group_name
    stmt2 = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.team))
    )
    refreshed = (await db.execute(stmt2)).scalar_one()
    return _user_response(refreshed)
