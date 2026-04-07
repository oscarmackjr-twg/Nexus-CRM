from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_role
from backend.models import Team, User
from backend.schemas.admin_groups import GroupCreate, GroupResponse, GroupUpdate

router = APIRouter(prefix="/admin/groups", tags=["admin"])


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    include_inactive: bool = False,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[GroupResponse]:
    stmt = (
        select(Team, func.count(User.id).label("member_count"))
        .outerjoin(User, User.team_id == Team.id)
        .where(Team.org_id == current_user.org_id)
        .group_by(Team.id)
    )
    if not include_inactive:
        stmt = stmt.where(Team.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    rows = result.all()
    return [
        GroupResponse(
            id=row[0].id,
            name=row[0].name,
            is_active=row[0].is_active,
            member_count=row[1],
            created_at=row[0].created_at,
        )
        for row in rows
    ]


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> GroupResponse:
    team = Team(
        org_id=current_user.org_id,
        name=payload.name,
        type="sales",
        is_active=True,
    )
    db.add(team)
    await db.flush()
    await db.commit()
    await db.refresh(team)
    return GroupResponse(
        id=team.id,
        name=team.name,
        is_active=team.is_active,
        member_count=0,
        created_at=team.created_at,
    )


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    payload: GroupUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> GroupResponse:
    team = await db.scalar(
        select(Team).where(Team.id == group_id, Team.org_id == current_user.org_id)
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if payload.name is not None:
        team.name = payload.name
    if payload.is_active is not None:
        team.is_active = payload.is_active

    await db.flush()
    # Re-query with member count
    stmt = (
        select(Team, func.count(User.id).label("member_count"))
        .outerjoin(User, User.team_id == Team.id)
        .where(Team.id == group_id)
        .group_by(Team.id)
    )
    row = (await db.execute(stmt)).one()
    await db.commit()
    return GroupResponse(
        id=row[0].id,
        name=row[0].name,
        is_active=row[0].is_active,
        member_count=row[1],
        created_at=row[0].created_at,
    )
