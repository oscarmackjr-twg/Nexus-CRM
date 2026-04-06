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


def contact_name_expr(first_name_col, last_name_col):
    from sqlalchemy import func as sa_func, literal
    return sa_func.trim(first_name_col + literal(" ") + last_name_col)


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


async def deal_activity_subqueries(session: AsyncSession, deal_ids: list[UUID]) -> dict:
    """Return activity summary subquery results keyed by deal_id (stub)."""
    return {}
