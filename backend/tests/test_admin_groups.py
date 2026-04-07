"""
Integration tests for Admin Groups API (17-02).

Covers GROUP-01, GROUP-02, GROUP-03, GROUP-04, GROUP-05.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_groups(async_client, seeded_org):
    """GET /api/v1/admin/groups returns 200 with list containing member_count."""
    headers = auth_header(seeded_org["admin"])
    response = await async_client.get("/api/v1/admin/groups", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for group in data:
        assert "member_count" in group
        assert "id" in group
        assert "name" in group
        assert "is_active" in group


@pytest.mark.asyncio
async def test_list_groups_excludes_inactive(async_client, seeded_org):
    """GET /api/v1/admin/groups without include_inactive omits deactivated groups."""
    headers = auth_header(seeded_org["admin"])
    alpha_id = str(seeded_org["alpha"].id)
    await async_client.patch(
        f"/api/v1/admin/groups/{alpha_id}",
        headers=headers,
        json={"is_active": False},
    )
    response = await async_client.get("/api/v1/admin/groups", headers=headers)
    assert response.status_code == 200
    data = response.json()
    ids = [g["id"] for g in data]
    assert alpha_id not in ids


@pytest.mark.asyncio
async def test_list_groups_includes_inactive(async_client, seeded_org):
    """GET /api/v1/admin/groups?include_inactive=true includes deactivated groups."""
    headers = auth_header(seeded_org["admin"])
    alpha_id = str(seeded_org["alpha"].id)
    await async_client.patch(
        f"/api/v1/admin/groups/{alpha_id}",
        headers=headers,
        json={"is_active": False},
    )
    response = await async_client.get(
        "/api/v1/admin/groups", headers=headers, params={"include_inactive": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    ids = [g["id"] for g in data]
    assert alpha_id in ids


@pytest.mark.asyncio
async def test_non_admin_forbidden_list(async_client, seeded_org):
    """GET /api/v1/admin/groups with regular_user token returns 403."""
    headers = auth_header(seeded_org["alpha-rep"])
    response = await async_client.get("/api/v1/admin/groups", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_group(async_client, seeded_org):
    """POST /api/v1/admin/groups returns 201 with is_active=true."""
    headers = auth_header(seeded_org["admin"])
    response = await async_client.post(
        "/api/v1/admin/groups", headers=headers, json={"name": "Gamma"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gamma"
    assert data["is_active"] is True
    assert data["member_count"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_non_admin_forbidden_create(async_client, seeded_org):
    """POST /api/v1/admin/groups with regular_user token returns 403."""
    headers = auth_header(seeded_org["alpha-rep"])
    response = await async_client.post(
        "/api/v1/admin/groups", headers=headers, json={"name": "Gamma"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_rename_group(async_client, seeded_org):
    """PATCH /api/v1/admin/groups/{id} with name returns 200."""
    headers = auth_header(seeded_org["admin"])
    create_response = await async_client.post(
        "/api/v1/admin/groups", headers=headers, json={"name": "ToRename"}
    )
    group_id = create_response.json()["id"]
    response = await async_client.patch(
        f"/api/v1/admin/groups/{group_id}",
        headers=headers,
        json={"name": "Renamed"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_deactivate_group(async_client, seeded_org):
    """PATCH /api/v1/admin/groups/{id} with is_active=false returns 200."""
    headers = auth_header(seeded_org["admin"])
    create_response = await async_client.post(
        "/api/v1/admin/groups", headers=headers, json={"name": "ToDeactivate"}
    )
    group_id = create_response.json()["id"]
    response = await async_client.patch(
        f"/api/v1/admin/groups/{group_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
