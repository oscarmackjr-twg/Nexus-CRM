from __future__ import annotations

import math
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


def clamp_pagination(page: int, size: int, max_size: int = 200) -> tuple[int, int]:
    page = max(1, page)
    size = max(1, min(size, max_size))
    return page, size


def page_count(total: int, size: int) -> int:
    if size <= 0:
        return 0
    return math.ceil(total / size)


async def count_rows(session: AsyncSession, stmt: Select) -> int:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await session.execute(count_stmt)
    return result.scalar_one()


def contact_name_expr():
    """SQL expression for contact full name (Contact model must be joined)."""
    from sqlalchemy import func as sa_func, literal
    from backend.models import Contact
    return sa_func.trim(
        sa_func.coalesce(Contact.first_name, literal("")) + literal(" ") + sa_func.coalesce(Contact.last_name, literal(""))
    )


async def accessible_team_ids(session: AsyncSession, user) -> list[UUID]:
    """Return team IDs visible to user — currently returns user's own team only."""
    if user.team_id:
        return [user.team_id]
    return []


def apply_tag_filter(stmt: Select, tags_col, tags: list[str]) -> Select:
    if not tags:
        return stmt
    from sqlalchemy import or_
    conditions = [tags_col.ilike(f"%{tag}%") for tag in tags]
    return stmt.where(or_(*conditions))


async def ensure_company_in_org(session: AsyncSession, company_id: UUID, org_id: UUID) -> None:
    from backend.models import Company
    from fastapi import HTTPException, status
    result = await session.execute(
        select(Company).where(Company.id == company_id, Company.org_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")


def deal_activity_subqueries(dialect_name: str):
    """Return 4 SQL column expressions for deal age/rotting calculation.
    Returns: (_, _, days_in_stage, is_rotting)
    """
    from sqlalchemy import case, cast, func, Integer, literal
    from backend.models import Deal, PipelineStage

    if dialect_name == "postgresql":
        days_in_stage = cast(
            func.extract("epoch", func.now() - Deal.updated_at) / 86400,
            Integer,
        )
    else:
        # SQLite
        days_in_stage = cast(
            func.julianday("now") - func.julianday(Deal.updated_at),
            Integer,
        )

    is_rotting = case(
        (
            (PipelineStage.rotting_days.isnot(None)) & (days_in_stage > PipelineStage.rotting_days),
            True,
        ),
        else_=False,
    )

    return (None, None, days_in_stage, is_rotting)


def user_name_expr():
    """SQL expression for user display name (User model must be joined)."""
    from sqlalchemy import func as sa_func
    from backend.models import User
    return sa_func.coalesce(User.full_name, User.username)


def merge_custom_fields(existing: dict, updates: dict) -> dict:
    """Merge update dict into existing custom_fields, removing None values."""
    merged = dict(existing or {})
    for key, value in (updates or {}).items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return merged


def is_admin(user) -> bool:
    return getattr(user, "role", None) in ("org_admin", "super_admin", "admin")


def is_manager_plus(user) -> bool:
    return getattr(user, "role", None) in ("manager", "org_admin", "super_admin", "admin")


def ensure_owner_or_admin(owner_id: UUID, user) -> None:
    from fastapi import HTTPException, status
    if not is_admin(user) and user.id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised")


async def ensure_contact_in_org(session: AsyncSession, contact_id: UUID, org_id: UUID) -> None:
    from backend.models import Contact
    from fastapi import HTTPException, status
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id, Contact.org_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


async def ensure_team_in_org(session: AsyncSession, team_id: UUID, org_id: UUID) -> None:
    from backend.models import Team
    from fastapi import HTTPException, status
    result = await session.execute(
        select(Team).where(Team.id == team_id, Team.org_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")


def utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def private_deal_predicate(user, visible_team_ids=None):
    """Return a WHERE clause that hides private deals the user doesn't own."""
    from sqlalchemy import or_
    from backend.models import Deal
    return or_(Deal.is_private == False, Deal.owner_id == user.id)  # noqa: E712
