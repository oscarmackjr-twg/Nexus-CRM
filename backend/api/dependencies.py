from __future__ import annotations

from fastapi import Depends, HTTPException, status

from backend.auth.security import get_current_user
from backend.database import get_db_session

# Canonical alias used by all routes
get_db = get_db_session


def require_role(*roles: str):
    """Return a FastAPI dependency that enforces one of the given roles."""

    async def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role!r} not permitted; requires one of {roles}",
            )
        return current_user

    return _check


__all__ = ["get_current_user", "get_db", "require_role"]
