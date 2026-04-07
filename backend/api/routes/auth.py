from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from redis import asyncio as redis_async
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemas import LogoutRequest, RefreshTokenRequest, Token, UserCreate, UserResponse, UserUpdate
from backend.auth.security import (
    create_access_token,
    create_refresh_token,
    encrypt_linkedin_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_token,
)
from backend.api.dependencies import require_role
from backend.config import settings
from backend.database import get_db_session
from backend.models import Organization, Team, User

router = APIRouter(tags=["auth"])

REFRESH_TTL_SECONDS = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_redis():
    return redis_async.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


def _refresh_key(token: str) -> str:
    return f"auth:refresh:{token}"


def _blacklist_key(token: str) -> str:
    return f"auth:blacklist:{token}"


def _build_token_payload(user: User) -> dict[str, str]:
    return {"sub": str(user.id), "org_id": str(user.org_id), "role": user.role}


def _slugify(value: str) -> str:
    slug = "-".join(value.lower().strip().split())
    return slug[:100] or "org"


async def _store_refresh_token(token: str, user_id: UUID) -> None:
    redis_client = _get_redis()
    try:
        await redis_client.set(_refresh_key(token), str(user_id), ex=REFRESH_TTL_SECONDS)
    finally:
        await redis_client.aclose()


async def _revoke_refresh_token(token: str) -> None:
    redis_client = _get_redis()
    try:
        await redis_client.set(_blacklist_key(token), "1", ex=REFRESH_TTL_SECONDS)
        await redis_client.delete(_refresh_key(token))
    finally:
        await redis_client.aclose()


async def _assert_refresh_token_usable(token: str) -> dict[str, Any]:
    payload = verify_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    redis_client = _get_redis()
    try:
        if await redis_client.exists(_blacklist_key(token)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
        stored_user_id = await redis_client.get(_refresh_key(token))
    finally:
        await redis_client.aclose()

    if stored_user_id != str(payload.get("sub")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognized")
    return payload


async def _issue_token_pair(user: User) -> Token:
    payload = _build_token_payload(user)
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    await _store_refresh_token(refresh_token, user.id)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def _get_user_by_identity(db: AsyncSession, identity: str) -> User | None:
    stmt = select(User).where(or_(User.email == identity, User.username == identity))
    return await db.scalar(stmt)


async def _get_team_in_org(db: AsyncSession, org_id: UUID, team_id: UUID | None) -> Team | None:
    if team_id is None:
        return None
    return await db.scalar(select(Team).where(Team.id == team_id, Team.org_id == org_id))


async def _assert_unique_user_fields(
    db: AsyncSession,
    email: str,
    username: str,
    exclude_user_id: UUID | None = None,
) -> None:
    email_owner = await db.scalar(select(User).where(User.email == email))
    if email_owner is not None and email_owner.id != exclude_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
    username_owner = await db.scalar(select(User).where(User.username == username))
    if username_owner is not None and username_owner.id != exclude_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already in use")


def _ensure_same_org(actor: User, org_id: UUID) -> None:
    if actor.role != "admin" and actor.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    user = await _get_user_by_identity(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    user.last_login = _utcnow()
    await db.commit()
    await db.refresh(user)
    return await _issue_token_pair(user)


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    await _assert_unique_user_fields(db, str(payload.email), payload.username)

    role = payload.role.value
    if payload.org_id is None:
        base_slug = _slugify(payload.username or str(payload.email).split("@")[0])
        slug = base_slug
        suffix = 1
        while await db.scalar(select(Organization).where(Organization.slug == slug)) is not None:
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        org = Organization(name=payload.full_name or payload.username, slug=slug, plan="free")
        db.add(org)
        await db.flush()
        role = "admin"
    else:
        org = await db.scalar(select(Organization).where(Organization.id == payload.org_id))
        if org is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    team = await _get_team_in_org(db, org.id, payload.team_id)
    if payload.team_id is not None and team is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in organization")

    user = User(
        org_id=org.id,
        email=str(payload.email),
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role,
        team_id=payload.team_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _issue_token_pair(user)


@router.post("/auth/refresh", response_model=Token)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> Token:
    token_payload = await _assert_refresh_token_usable(payload.refresh_token)
    user_id = token_payload.get("sub")
    user = await db.scalar(select(User).where(User.id == UUID(str(user_id))))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")
    await _revoke_refresh_token(payload.refresh_token)
    return await _issue_token_pair(user)


@router.post("/auth/logout")
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    token_payload = verify_token(payload.refresh_token)
    if token_payload.get("type") != "refresh" or token_payload.get("sub") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    await _revoke_refresh_token(payload.refresh_token)
    return {"status": "logged_out"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/auth/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    if payload.role is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role cannot be updated here")
    if payload.team_id is not None or payload.is_active is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted fields in profile update")
    if payload.email is not None or payload.username is not None:
        await _assert_unique_user_fields(
            db,
            str(payload.email or current_user.email),
            payload.username or current_user.username,
            exclude_user_id=current_user.id,
        )
    if payload.email is not None:
        current_user.email = str(payload.email)
    if payload.username is not None:
        current_user.username = payload.username
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.password is not None:
        current_user.hashed_password = hash_password(payload.password)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    stmt = select(User).where(User.org_id == current_user.org_id)
    count_stmt = select(func.count()).select_from(User).where(User.org_id == current_user.org_id)
    filters = []
    if role:
        filters.append(User.role == role)
    if team_id:
        filters.append(User.team_id == team_id)
    if search:
        term = f"%{search}%"
        filters.append(or_(User.full_name.ilike(term), User.email.ilike(term), User.username.ilike(term)))
    for condition in filters:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    total = await db.scalar(count_stmt) or 0
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    users = (await db.scalars(stmt)).all()
    return {
        "items": [UserResponse.model_validate(user).model_dump(mode="json") for user in users],
        "page": page,
        "size": size,
        "total": total,
    }


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    await _assert_unique_user_fields(db, str(payload.email), payload.username)
    team = await _get_team_in_org(db, current_user.org_id, payload.team_id)
    if payload.team_id is not None and team is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in organization")
    user = User(
        org_id=current_user.org_id,
        email=str(payload.email),
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role.value,
        team_id=payload.team_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _ensure_same_org(current_user, user.org_id)

    is_admin = current_user.role in {"admin"}
    is_self = current_user.id == user.id
    if not is_admin and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not is_admin and (payload.role is not None or payload.team_id is not None or payload.is_active is not None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Restricted fields")

    next_email = str(payload.email) if payload.email is not None else user.email
    next_username = payload.username or user.username
    if payload.email is not None or payload.username is not None:
        await _assert_unique_user_fields(db, next_email, next_username, exclude_user_id=user.id)

    if payload.team_id is not None:
        team = await _get_team_in_org(db, user.org_id, payload.team_id)
        if team is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team not found in organization")
        user.team_id = payload.team_id
    if payload.email is not None:
        user.email = str(payload.email)
    if payload.username is not None:
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)
    if is_admin and payload.role is not None:
        user.role = payload.role.value
    if is_admin and payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _ensure_same_org(current_user, user.org_id)
    if current_user.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
    user.is_active = False
    await db.commit()
    return {"status": "deactivated"}


@router.post("/auth/linkedin/connect")
async def linkedin_connect(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    state = create_access_token(
        {
            "sub": str(current_user.id),
            "org_id": str(current_user.org_id),
            "purpose": "linkedin_oauth",
        }
    )
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "scope": "openid profile email",
            "state": state,
        }
    )
    return {"auth_url": f"https://www.linkedin.com/oauth/v2/authorization?{query}"}


@router.get("/auth/linkedin/callback")
async def linkedin_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    state_payload = verify_token(state)
    if state_payload.get("purpose") != "linkedin_oauth":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid state")

    user = await db.scalar(select(User).where(User.id == UUID(str(state_payload["sub"]))))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
        )
        token_response.raise_for_status()
        token_payload = token_response.json()
        access_token = token_payload["access_token"]
        member_response = await client.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        member_response.raise_for_status()
        member_payload = member_response.json()

    user.linkedin_access_token = encrypt_linkedin_token(access_token)
    user.linkedin_member_id = str(member_payload.get("id"))
    expires_in = int(token_payload.get("expires_in", 0))
    user.linkedin_token_expiry = _utcnow() if expires_in <= 0 else _utcnow().replace(microsecond=0) + timedelta(seconds=expires_in)
    await db.commit()

    frontend_origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else ""
    redirect_target = f"{frontend_origin}/linkedin/connected" if frontend_origin else "/linkedin/connected"
    return RedirectResponse(url=redirect_target, status_code=status.HTTP_302_FOUND)
