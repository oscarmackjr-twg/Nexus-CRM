from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status


# ── Role helpers ─────────────────────────────────────────────────────────────

def is_admin(user) -> bool:
    return getattr(user, "role", None) == "admin"


def is_principal(user) -> bool:
    return getattr(user, "role", None) == "principal"


def is_supervisor(user) -> bool:
    return getattr(user, "role", None) == "supervisor"


def is_oversight_role(user) -> bool:
    """Supervisor, Principal, or Admin — all can see private deals within their scope."""
    return getattr(user, "role", None) in ("supervisor", "principal", "admin")


# ── List/read scoping ────────────────────────────────────────────────────────

def visible_deal_team_ids(user) -> list[UUID] | None:
    """
    Return the set of team_ids for SQL WHERE scoping.
    - None  -> no team filter (Admin and Principal see all teams)
    - list  -> filter to Deal.team_id IN (list)
    - []    -> no deals visible (user has no team assignment)

    Per D-05/D-06: admin & principal see all; supervisor & regular_user own team only.
    """
    if is_admin(user) or is_principal(user):
        return None  # All teams visible
    if user.team_id is None:
        return []    # Unassigned user sees nothing
    return [user.team_id]


def private_deal_predicate(user):
    """
    Returns a SQLAlchemy clause restricting private deals.
    - Admin / Principal / Supervisor: no restriction (oversight roles see all private deals, D-11)
    - Regular User: can only see private deals they own
    """
    from backend.models import Deal
    if is_oversight_role(user):
        return True  # No restriction — SQLAlchemy accepts True as a no-op WHERE clause
    return or_(Deal.is_private.is_(False), Deal.owner_id == user.id)


# ── Action permission checks (pure bool, no DB) ──────────────────────────────

def can_read_deal(user, deal) -> bool:
    """True if user can read this specific deal."""
    if is_admin(user) or is_principal(user):
        return True
    if user.team_id is None or deal.team_id != user.team_id:
        return False
    # Same team — check is_private for regular_user
    if user.role == "regular_user" and deal.is_private and deal.owner_id != user.id:
        return False
    return True


def can_write_deal(user, deal) -> bool:
    """True if user can update this deal (field edits, stage moves). Per D-06/D-08/D-10."""
    if is_admin(user):
        return True
    if is_supervisor(user):
        # D-08: supervisor can edit any deal in their group
        return user.team_id is not None and deal.team_id == user.team_id
    # Principal and Regular User: own deals only (D-06/D-10)
    return deal.owner_id == user.id


def can_delete_deal(user, deal) -> bool:
    """True if user can delete this deal. Per D-07: owner or admin only."""
    if is_admin(user):
        return True
    return deal.owner_id == user.id  # All non-admin roles: own deals only


# ── Async guards (DB + 403/404 decision) ─────────────────────────────────────

async def require_deal_readable(db: AsyncSession, deal_id: UUID, user) -> "Deal":
    """
    Load deal scoped to org only (no team filter), return it if readable.
    Raises 404 if not found in org, 403 if user cannot read it.

    Per D-01/D-02: clean 403-vs-404 split.
    Use this in child services (counterparties, funding) and deal detail actions.
    """
    from backend.models import Deal
    deal = await db.scalar(
        select(Deal).where(Deal.id == deal_id, Deal.org_id == user.org_id)
    )
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not can_read_deal(user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return deal


async def require_deal_writable(db: AsyncSession, deal_id: UUID, user) -> "Deal":
    """
    Load deal, return it if user can write to it.
    Raises 404 if not found, 403 if read-forbidden or write-forbidden.
    """
    deal = await require_deal_readable(db, deal_id, user)
    if not can_write_deal(user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return deal
