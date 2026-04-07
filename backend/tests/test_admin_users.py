"""
Integration tests for Admin Users API (17-02).

Covers ADMIN-10, ADMIN-11, GROUP-05.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_users(async_client, seeded_org):
    """GET /api/v1/admin/users returns 200 + list with group_name and role fields."""
    headers = auth_header(seeded_org["admin"])
    response = await async_client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for user in data:
        assert "role" in user
        assert "group_name" in user
        assert "id" in user
        assert "email" in user


@pytest.mark.asyncio
async def test_user_list_includes_role(async_client, seeded_org):
    """Response objects contain role and group_name fields with correct values."""
    headers = auth_header(seeded_org["admin"])
    response = await async_client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    admin_user = next((u for u in data if u["email"] == "admin@example.com"), None)
    assert admin_user is not None
    assert admin_user["role"] == "admin"
    assert admin_user["group_name"] == "Alpha"


@pytest.mark.asyncio
async def test_non_admin_forbidden_list(async_client, seeded_org):
    """GET /api/v1/admin/users with regular_user token returns 403."""
    headers = auth_header(seeded_org["alpha-rep"])
    response = await async_client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user(async_client, seeded_org):
    """POST /api/v1/admin/users with valid payload returns 201."""
    headers = auth_header(seeded_org["admin"])
    response = await async_client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "full_name": "New User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "regular_user",
            "team_id": str(seeded_org["alpha"].id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "regular_user"


@pytest.mark.asyncio
async def test_non_admin_forbidden_create(async_client, seeded_org):
    """POST /api/v1/admin/users with regular_user token returns 403."""
    headers = auth_header(seeded_org["alpha-rep"])
    response = await async_client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "full_name": "New User",
            "email": "another@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_role(async_client, seeded_org):
    """PATCH /api/v1/admin/users/{id} with role update returns 200."""
    headers = auth_header(seeded_org["admin"])
    rep_id = str(seeded_org["alpha-rep"].id)
    response = await async_client.patch(
        f"/api/v1/admin/users/{rep_id}",
        headers=headers,
        json={"role": "supervisor"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "supervisor"


@pytest.mark.asyncio
async def test_group_assignment(async_client, seeded_org):
    """PATCH /api/v1/admin/users/{id} with team_id moves user to new group."""
    headers = auth_header(seeded_org["admin"])
    rep_id = str(seeded_org["alpha-rep"].id)
    beta_id = str(seeded_org["beta"].id)
    response = await async_client.patch(
        f"/api/v1/admin/users/{rep_id}",
        headers=headers,
        json={"team_id": beta_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == beta_id


@pytest.mark.asyncio
async def test_invalid_role_returns_400(async_client, seeded_org):
    """PATCH /api/v1/admin/users/{id} with invalid role returns 400."""
    headers = auth_header(seeded_org["admin"])
    rep_id = str(seeded_org["alpha-rep"].id)
    response = await async_client.patch(
        f"/api/v1/admin/users/{rep_id}",
        headers=headers,
        json={"role": "superuser"},
    )
    assert response.status_code == 400
