from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from backend.models import Company, Contact, Deal, Organization, PipelineStage, User
from backend.seed_data import seed
from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_registration_profile_and_user_management_error_paths(async_client, seeded_org):
    created = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "new-owner@example.com", "username": "new-owner", "password": "secret123", "full_name": "New Owner"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["token_type"] == "bearer"
    assert (await async_client.post(
        "/api/v1/auth/register",
        json={"email": "new-owner@example.com", "username": "other-owner", "password": "secret123"},
    )).status_code == 400

    admin_headers = auth_header(seeded_org["admin"])
    assert (await async_client.put("/api/v1/auth/me", headers=admin_headers, json={"role": "supervisor"})).status_code == 403
    changed = await async_client.put(
        "/api/v1/auth/me", headers=admin_headers,
        json={"full_name": "Updated Admin", "username": "admin-updated", "password": "secret456"},
    )
    assert changed.status_code == 200 and changed.json()["username"] == "admin-updated"
    # Every mutation path preserves the signed-in administrator's active status.
    assert (await async_client.put(
        f"/api/v1/users/{seeded_org['admin'].id}", headers=admin_headers, json={"is_active": False},
    )).status_code == 400
    assert (await async_client.delete(f"/api/v1/users/{seeded_org['admin'].id}", headers=admin_headers)).status_code == 400


@pytest.mark.asyncio
async def test_auth_rejects_invalid_refresh_logout_and_cross_org_user_update(async_client, seeded_org):
    headers = auth_header(seeded_org["admin"])
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})).status_code == 401
    assert (await async_client.post("/api/v1/auth/logout", headers=headers, json={"refresh_token": "not-a-token"})).status_code == 401
    assert (await async_client.put(f"/api/v1/users/{uuid4()}", headers=headers, json={"full_name": "Missing"})).status_code == 404
    assert (await async_client.post(
        "/api/v1/users", headers=headers,
        json={"email": "bad-team@example.com", "username": "bad-team", "password": "secret123", "team_id": str(uuid4())},
    )).status_code == 400


@pytest.mark.asyncio
async def test_seed_creates_a_complete_demo_and_is_idempotent(db_session):
    await seed()
    await seed()
    org = await db_session.scalar(select(Organization).where(Organization.slug == "demo-org"))
    assert org is not None
    assert await db_session.scalar(select(func.count()).select_from(Company).where(Company.org_id == org.id)) == 4
    assert await db_session.scalar(select(func.count()).select_from(Contact).where(Contact.org_id == org.id)) == 6
    assert await db_session.scalar(select(func.count()).select_from(Deal).where(Deal.org_id == org.id)) == 6


@pytest.mark.asyncio
async def test_health_readiness_liveness_and_metrics(async_client, monkeypatch):
    import backend.api.main as main

    assert (await async_client.get("/")).json()["service"] == "nexus-crm"
    assert (await async_client.get("/health")).status_code == 200
    ready = await async_client.get("/health/ready")
    assert ready.status_code == 200 and ready.json()["status"] == "ready"
    assert (await async_client.get("/health/live")).json() == {"status": "alive"}
    main.app.state.metrics_renderer = lambda: "nexus_metric 1\n"
    assert "nexus_metric" in (await async_client.get("/metrics")).text

    async def unavailable():
        raise RuntimeError("offline")

    monkeypatch.setattr(main, "check_redis", unavailable)
    degraded = await async_client.get("/health/ready")
    assert degraded.status_code == 503 and degraded.json()["checks"]["redis"]["status"] == "error"


@pytest.mark.asyncio
async def test_lifespan_and_production_metrics_authorization(async_client, monkeypatch):
    import backend.api.main as main

    events: list[str] = []

    class FakeConnection:
        async def run_sync(self, callback):
            events.append("schema_created")

    class FakeBegin:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, *args):
            return None

    class FakeEngine:
        def begin(self):
            return FakeBegin()

        async def dispose(self):
            events.append("engine_closed")

    class FakeRedis:
        async def aclose(self):
            events.append("redis_closed")

    engine = FakeEngine()
    monkeypatch.setattr(main, "setup_logging", lambda settings: events.append("logging_started"))
    monkeypatch.setattr(main, "get_engine", lambda: engine)
    monkeypatch.setattr(main.redis_async, "from_url", lambda *args, **kwargs: FakeRedis())
    monkeypatch.setattr(main, "setup_telemetry", lambda app, settings: events.append("telemetry_started"))
    monkeypatch.setattr(main, "install_signal_handlers", lambda app, celery: events.append("signals_installed"))

    async with main.lifespan(main.app):
        assert main.app.state.db_engine is engine
        assert events == ["logging_started", "schema_created", "telemetry_started", "signals_installed"]
    assert events[-2:] == ["redis_closed", "engine_closed"]

    monkeypatch.setattr(main.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(main.settings, "METRICS_API_KEY", "metrics-secret")
    main.app.state.metrics_renderer = lambda: "secured_metric 1\n"
    assert (await async_client.get("/metrics")).status_code == 403
    assert (await async_client.get("/metrics", headers={"X-API-Key": "wrong"})).status_code == 403
    allowed = await async_client.get("/metrics", headers={"X-API-Key": "metrics-secret"})
    assert allowed.status_code == 200 and "secured_metric" in allowed.text


@pytest.mark.asyncio
async def test_crm_update_archive_and_deal_state_error_paths(async_client, seeded_org, pipeline, stages):
    headers = auth_header(seeded_org["alpha-rep"])
    company = await async_client.post("/api/v1/companies/", headers=headers, json={"name": "Coverage Holdings", "industry": "Tech", "tags": ["target"]})
    assert company.status_code == 201
    company_id = company.json()["id"]
    contact = await async_client.post(
        "/api/v1/contacts/", headers=headers,
        json={"first_name": "Coverage", "last_name": "Contact", "company_id": company_id, "tags": ["target"]},
    )
    assert contact.status_code == 201
    contact_id = contact.json()["id"]
    assert (await async_client.patch(f"/api/v1/companies/{company_id}", headers=headers, json={"watchlist": True, "tags": ["updated"]})).status_code == 200
    assert (await async_client.patch(f"/api/v1/contacts/{contact_id}", headers=headers, json={"lifecycle_stage": "customer", "tags": ["updated"]})).status_code == 200

    deal = await async_client.post(
        "/api/v1/deals/", headers=headers,
        json={"name": "Coverage Deal", "pipeline_id": str(pipeline.id), "stage_id": str(stages[0].id), "company_id": company_id, "contact_id": contact_id, "tags": ["coverage"]},
    )
    assert deal.status_code == 201, deal.text
    deal_id = deal.json()["id"]
    updated = await async_client.patch(
        f"/api/v1/deals/{deal_id}", headers=headers,
        json={"description": "Updated", "custom_fields": {"source": "test"}, "passed_dead_reasons": [], "tags": ["updated"]},
    )
    assert updated.status_code == 200 and updated.json()["custom_fields"]["source"] == "test"
    moved = await async_client.post(f"/api/v1/deals/{deal_id}/move-stage", headers=headers, json={"stage_id": str(stages[3].id), "log_activity": False})
    assert moved.status_code == 200 and moved.json()["status"] == "won"
    activity = await async_client.post(
        f"/api/v1/deals/{deal_id}/activities", headers=headers,
        json={"activity_type": "note", "title": "Covered", "is_private": True},
    )
    assert activity.status_code == 201
    assert (await async_client.get(f"/api/v1/deals/{deal_id}/activities?page=1&size=1", headers=headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)).status_code == 204
    assert (await async_client.get("/api/v1/contacts/?include_archived=true&search=Coverage", headers=headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/companies/{company_id}", headers=headers)).status_code == 204
    assert (await async_client.get("/api/v1/companies/?include_archived=true&search=Coverage", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_counterparty_missing_and_foreign_company_are_rejected(async_client, seeded_org, pipeline, stages):
    headers = auth_header(seeded_org["alpha-rep"])
    deal = await async_client.post(
        "/api/v1/deals/", headers=headers,
        json={"name": "Counterparty Guard", "pipeline_id": str(pipeline.id), "stage_id": str(stages[0].id)},
    )
    assert deal.status_code == 201
    deal_id = deal.json()["id"]
    assert (await async_client.patch(f"/api/v1/deals/{deal_id}/counterparties/{uuid4()}", headers=headers, json={"notes": "Missing"})).status_code == 404
    assert (await async_client.post(
        f"/api/v1/deals/{deal_id}/counterparties/", headers=headers, json={"company_id": str(uuid4())},
    )).status_code == 404
