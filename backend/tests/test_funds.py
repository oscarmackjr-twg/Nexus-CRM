"""Tests for Fund CRUD API — /api/v1/funds"""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio

from backend.auth.security import create_access_token, hash_password
from backend.models import Organization, Team, User


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def fund_seed(db_session):
    org = Organization(name="FundOrg", slug="fundorg")
    db_session.add(org)
    await db_session.flush()

    team = Team(org_id=org.id, name="FundTeam", type="sales")
    db_session.add(team)
    await db_session.flush()

    admin = User(
        org_id=org.id,
        email="fundadmin@example.com",
        username="fundadmin",
        hashed_password=hash_password("secret123"),
        full_name="Fund Admin",
        role="admin",
        team_id=team.id,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    return {"org": org, "team": team, "admin": admin}


@pytest.mark.asyncio
async def test_create_fund(client, fund_seed):
    """POST /api/v1/funds creates a new fund"""
    headers = auth_header(fund_seed["admin"])
    response = await client.post(
        "/api/v1/funds",
        json={"fund_name": "Test Fund I"},
        headers=headers,
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "id" in data
    assert data["fund_name"] == "Test Fund I"


@pytest.mark.asyncio
async def test_list_funds(client, fund_seed):
    """GET /api/v1/funds returns a list of funds for the org"""
    headers = auth_header(fund_seed["admin"])
    # Create a fund first
    await client.post(
        "/api/v1/funds",
        json={"fund_name": "List Test Fund"},
        headers=headers,
    )
    response = await client.get("/api/v1/funds", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_update_fund(client, fund_seed):
    """PATCH /api/v1/funds/{id} updates a fund's fields"""
    headers = auth_header(fund_seed["admin"])
    # Create a fund
    create_resp = await client.post(
        "/api/v1/funds",
        json={"fund_name": "Original Fund"},
        headers=headers,
    )
    assert create_resp.status_code in (200, 201)
    fund_id = create_resp.json()["id"]

    # Update the fund
    update_resp = await client.patch(
        f"/api/v1/funds/{fund_id}",
        json={"fund_name": "Updated Fund"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["fund_name"] == "Updated Fund"


@pytest.mark.asyncio
async def test_fund_not_found(client, fund_seed):
    """PATCH /api/v1/funds/{random_uuid} returns 404"""
    headers = auth_header(fund_seed["admin"])
    response = await client.patch(
        f"/api/v1/funds/{uuid4()}",
        json={"fund_name": "Ghost Fund"},
        headers=headers,
    )
    assert response.status_code == 404
