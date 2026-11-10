"""Public authentication route regressions used by the coverage restoration tranche."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.api.routes import auth
from backend.auth.schemas import UserCreate, UserUpdate
from backend.auth.security import create_access_token, create_refresh_token
from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_login_refresh_logout_and_me(async_client, seeded_org):
    login = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "secret123"},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"

    refreshed = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200, refreshed.text

    logged_out = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
        json={"refresh_token": refreshed.json()["refresh_token"]},
    )
    assert logged_out.status_code == 200
    assert logged_out.json() == {"status": "logged_out"}


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials_and_users_list_filters(async_client, seeded_org):
    denied = await async_client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "wrong"})
    assert denied.status_code == 401

    headers = auth_header(seeded_org["admin"])
    response = await async_client.get("/api/v1/users?role=regular_user&search=alpha&page=1&size=5", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_profile_update_rejects_unauthenticated_request(async_client, seeded_org):
    assert (await async_client.get("/api/v1/auth/me")).status_code == 401
    headers = auth_header(seeded_org["alpha-rep"])
    updated = await async_client.put("/api/v1/auth/me", headers=headers, json={"full_name": "Updated Rep"})
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Rep"


@pytest.mark.asyncio
async def test_refresh_and_logout_reject_revoked_wrong_or_unavailable_tokens(async_client, db_session, seeded_org):
    login = await async_client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    tokens = login.json()

    wrong_type = create_access_token({"sub": str(seeded_org["admin"].id)})
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": wrong_type})).status_code == 401
    unknown = create_refresh_token({"sub": str(seeded_org["admin"].id)})
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": unknown})).status_code == 401

    mismatched_logout = await async_client.post(
        "/api/v1/auth/logout",
        headers=auth_header(seeded_org["alpha-rep"]),
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert mismatched_logout.status_code == 401
    revoked = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert revoked.status_code == 200
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code == 401

    available = await async_client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "secret123"}
    )
    seeded_org["admin"].is_active = False
    await db_session.commit()
    assert (await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": available.json()["refresh_token"]}
    )).status_code == 401


@pytest.mark.asyncio
async def test_registration_slug_collision_and_unique_identity_errors(async_client, seeded_org):
    collision = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "collision-owner@example.com", "username": "acme", "password": "secret123"},
    )
    assert collision.status_code == 201
    assert (await async_client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "username": "unused-name", "password": "secret123"},
    )).status_code == 400
    assert (await async_client.post(
        "/api/v1/auth/register",
        json={"email": "unique-email@example.com", "username": "admin", "password": "secret123"},
    )).status_code == 400


@pytest.mark.asyncio
async def test_profile_and_admin_user_updates_cover_mutable_fields(async_client, seeded_org):
    rep_headers = auth_header(seeded_org["alpha-rep"])
    assert (await async_client.put(
        "/api/v1/auth/me", headers=rep_headers, json={"team_id": str(seeded_org["beta"].id)},
    )).status_code == 403
    profile = await async_client.put(
        "/api/v1/auth/me", headers=rep_headers,
        json={
            "email": "alpha-renamed@example.com", "username": "alpha-renamed", "full_name": "Alpha Renamed",
            "avatar_url": "https://example.com/avatar.png", "password": "new-secret123",
        },
    )
    assert profile.status_code == 200 and profile.json()["username"] == "alpha-renamed"

    admin_headers = auth_header(seeded_org["admin"])
    created = await async_client.post(
        "/api/v1/users", headers=admin_headers,
        json={"email": "plain-user@example.com", "username": "plain-user", "password": "secret123"},
    )
    assert created.status_code == 201
    updated = await async_client.put(
        f"/api/v1/users/{seeded_org['alpha-peer'].id}", headers=admin_headers,
        json={
            "email": "peer-renamed@example.com", "username": "peer-renamed", "full_name": "Peer Renamed",
            "avatar_url": "https://example.com/peer.png", "password": "peer-secret123", "role": "supervisor", "is_active": True,
        },
    )
    assert updated.status_code == 200 and updated.json()["email"] == "peer-renamed@example.com"


@pytest.mark.asyncio
async def test_inactive_login_and_cross_organization_user_update_are_rejected(async_client, db_session, seeded_org):
    seeded_org["alpha-rep"].is_active = False
    await db_session.commit()
    assert (await async_client.post(
        "/api/v1/auth/login", data={"username": "alpha-rep@example.com", "password": "secret123"},
    )).status_code == 401

    outsider = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "outsider@example.com", "username": "outsider", "password": "secret123"},
    )
    assert outsider.status_code == 201
    outsider_member = await async_client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {outsider.json()['access_token']}"},
        json={
            "email": "outsider-member@example.com", "username": "outsider-member", "password": "secret123",
            "role": "regular_user",
        },
    )
    assert outsider_member.status_code == 201
    outsider_member_login = await async_client.post(
        "/api/v1/auth/login", data={"username": "outsider-member", "password": "secret123"},
    )
    assert outsider_member_login.status_code == 200
    assert (await async_client.put(
        f"/api/v1/users/{seeded_org['alpha-peer'].id}",
        headers={"Authorization": f"Bearer {outsider_member_login.json()['access_token']}"},
        json={"full_name": "Forbidden"},
    )).status_code == 403


@pytest.mark.asyncio
async def test_auth_route_handlers_cover_registration_and_user_mutations(db_session, fake_redis, seeded_org):
    with pytest.raises(HTTPException):
        await auth._assert_unique_user_fields(db_session, "admin@example.com", "available-name")
    with pytest.raises(HTTPException):
        await auth._assert_unique_user_fields(db_session, "available@example.com", "admin")

    registered = await auth.register(
        UserCreate(email="direct-owner@example.com", username="direct-owner", password="secret123"), db_session
    )
    assert registered.access_token

    admin = seeded_org["admin"]
    created = await auth.create_user(
        UserCreate(email="direct-user@example.com", username="direct-user", password="secret123"), admin, db_session
    )
    assert created.username == "direct-user"

    profile = await auth.update_me(
        UserUpdate(
            email="alpha-direct@example.com", username="alpha-direct", full_name="Alpha Direct",
            avatar_url="https://example.com/direct.png", password="direct-secret123",
        ),
        seeded_org["alpha-rep"],
        db_session,
    )
    assert profile.username == "alpha-direct"

    updated = await auth.update_user(
        seeded_org["alpha-peer"].id,
        UserUpdate(
            email="peer-direct@example.com", username="peer-direct", full_name="Peer Direct",
            avatar_url="https://example.com/peer.png", password="peer-secret123", role="supervisor", is_active=True,
        ),
        admin,
        db_session,
    )
    assert updated.role == "supervisor"
