from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest

from backend.auth.security import create_access_token
from backend.config import settings
from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_registration_validates_organization_and_team_membership(async_client, seeded_org):
    # Joining an existing org through public registration is refused, whether or
    # not the org exists, so the endpoint does not reveal which org IDs are valid.
    joined = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "team-member@example.com", "username": "team-member", "password": "secret123",
            "org_id": str(seeded_org["org"].id), "team_id": str(seeded_org["alpha"].id), "role": "supervisor",
        },
    )
    assert joined.status_code == 403, joined.text
    assert (await async_client.post(
        "/api/v1/auth/register",
        json={"email": "missing-org@example.com", "username": "missing-org", "password": "secret123", "org_id": str(uuid4())},
    )).status_code == 403

    created_org = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "other-org@example.com", "username": "other-org", "password": "secret123"},
    )
    assert created_org.status_code == 201
    # A brand-new org has no teams, so any team_id is rejected.
    assert (await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong-team@example.com", "username": "wrong-team", "password": "secret123",
            "team_id": str(uuid4()),
        },
    )).status_code == 400


@pytest.mark.asyncio
async def test_registration_cannot_join_existing_org_as_admin(async_client, seeded_org):
    """Regression: anonymous self-registration must not grant a role in an existing org."""
    escalation = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder@example.com", "username": "intruder", "password": "secret123",
            "org_id": str(seeded_org["org"].id), "role": "admin",
        },
    )
    assert escalation.status_code == 403, escalation.text
    # No account was created.
    assert (await async_client.post(
        "/api/v1/auth/login", data={"username": "intruder", "password": "secret123"},
    )).status_code == 401

    # The supported path still works: an org admin adds the user, with the role the admin chooses.
    added = await async_client.post(
        "/api/v1/users",
        headers=auth_header(seeded_org["admin"]),
        json={
            "email": "invited@example.com", "username": "invited", "password": "secret123",
            "role": "regular_user",
        },
    )
    assert added.status_code == 201, added.text
    assert added.json()["role"] == "regular_user"


@pytest.mark.asyncio
async def test_user_list_filters_and_admin_lifecycle(async_client, seeded_org):
    admin_headers = auth_header(seeded_org["admin"])
    listed = await async_client.get(
        f"/api/v1/users?role=regular_user&team_id={seeded_org['alpha'].id}&search=alpha&page=1&size=1",
        headers=admin_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 2 and len(listed.json()["items"]) == 1

    created = await async_client.post(
        "/api/v1/users", headers=admin_headers,
        json={
            "email": "lifecycle@example.com", "username": "lifecycle", "password": "secret123",
            "full_name": "Lifecycle User", "role": "regular_user", "team_id": str(seeded_org["alpha"].id),
        },
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]
    updated = await async_client.put(
        f"/api/v1/users/{user_id}", headers=admin_headers,
        json={"role": "supervisor", "team_id": str(seeded_org["beta"].id), "is_active": False, "avatar_url": "https://example.test/a.png"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "supervisor" and updated.json()["team_id"] == str(seeded_org["beta"].id)
    assert (await async_client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/users/{uuid4()}", headers=admin_headers)).status_code == 404


@pytest.mark.asyncio
async def test_non_admin_user_mutation_restrictions(async_client, seeded_org):
    headers = auth_header(seeded_org["alpha-rep"])
    assert (await async_client.put(
        f"/api/v1/users/{seeded_org['alpha-peer'].id}", headers=headers, json={"full_name": "Nope"},
    )).status_code == 403
    assert (await async_client.put(
        f"/api/v1/users/{seeded_org['alpha-rep'].id}", headers=headers, json={"role": "admin"},
    )).status_code == 403
    assert (await async_client.delete(f"/api/v1/users/{seeded_org['alpha-peer'].id}", headers=headers)).status_code == 403


@pytest.mark.asyncio
async def test_linkedin_connect_and_callback_reject_invalid_states(async_client, seeded_org):
    assert (await async_client.post("/api/v1/auth/linkedin/connect")).status_code == 401
    headers = auth_header(seeded_org["admin"])
    connect = await async_client.post("/api/v1/auth/linkedin/connect", headers=headers)
    assert connect.status_code == 200 and "linkedin.com/oauth" in connect.json()["auth_url"]
    assert (await async_client.get("/api/v1/auth/linkedin/callback?code=ignored&state=not-a-token")).status_code == 401

    wrong_purpose = create_access_token({"sub": str(seeded_org["admin"].id), "org_id": str(seeded_org["org"].id)})
    assert (await async_client.get(f"/api/v1/auth/linkedin/callback?code=ignored&state={wrong_purpose}")).status_code == 401
    unavailable = create_access_token({"sub": str(uuid4()), "org_id": str(seeded_org["org"].id), "purpose": "linkedin_oauth"})
    assert (await async_client.get(f"/api/v1/auth/linkedin/callback?code=ignored&state={unavailable}")).status_code == 401


@pytest.mark.asyncio
async def test_linkedin_callback_persists_token_and_redirects(async_client, db_session, seeded_org, monkeypatch):
    requests: list[tuple[str, str, dict]] = []

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, data):
            requests.append(("post", url, data))
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={"access_token": "linkedin-access", "expires_in": 3600},
            )

        async def get(self, url, *, headers):
            requests.append(("get", url, headers))
            return httpx.Response(200, request=httpx.Request("GET", url), json={"id": "linkedin-member-42"})

    monkeypatch.setattr("backend.api.routes.auth.httpx.AsyncClient", lambda **kwargs: MockAsyncClient())
    state = create_access_token(
        {"sub": str(seeded_org["admin"].id), "org_id": str(seeded_org["org"].id), "purpose": "linkedin_oauth"}
    )

    response = await async_client.get(
        f"/api/v1/auth/linkedin/callback?code=authorization-code&state={state}", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"{settings.CORS_ORIGINS[0]}/linkedin/connected"
    assert requests == [
        ("post", "https://www.linkedin.com/oauth/v2/accessToken", {
            "grant_type": "authorization_code", "code": "authorization-code", "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID, "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }),
        ("get", "https://api.linkedin.com/v2/me", {"Authorization": "Bearer linkedin-access"}),
    ]

    await db_session.refresh(seeded_org["admin"])
    user = seeded_org["admin"]
    assert user.linkedin_member_id == "linkedin-member-42"
    assert user.linkedin_access_token and user.linkedin_access_token != "linkedin-access"
    assert user.linkedin_token_expiry is not None and user.linkedin_token_expiry > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_admin_user_validation_and_group_lifecycle_errors(async_client, seeded_org):
    headers = auth_header(seeded_org["admin"])
    assert (await async_client.post(
        "/api/v1/admin/users", headers=headers,
        json={"full_name": "Bad Role", "email": "bad-role@example.com", "password": "password123", "role": "owner"},
    )).status_code == 400

    generated_username = await async_client.post(
        "/api/v1/admin/users", headers=headers,
        json={"full_name": "Another Admin", "email": "admin@other.example.com", "password": "password123"},
    )
    assert generated_username.status_code == 201
    assert (await async_client.patch(
        f"/api/v1/admin/users/{seeded_org['alpha-rep'].id}", headers=headers, json={"team_id": str(uuid4())},
    )).status_code == 400

    assert (await async_client.post("/api/v1/admin/groups", headers=headers, json={"name": ""})).status_code == 422
    assert (await async_client.patch(
        f"/api/v1/admin/groups/{uuid4()}", headers=headers, json={"is_active": True},
    )).status_code == 404


@pytest.mark.asyncio
async def test_admin_cannot_remove_the_last_active_administrator(async_client, seeded_org):
    headers = auth_header(seeded_org["admin"])
    deactivate_other_admin = await async_client.patch(
        f"/api/v1/admin/users/{seeded_org['super'].id}", headers=headers, json={"is_active": False}
    )
    assert deactivate_other_admin.status_code == 200
    response = await async_client.patch(
        f"/api/v1/admin/users/{seeded_org['admin'].id}",
        headers=headers,
        json={"is_active": False},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot remove the last active administrator"
