"""Public API regression coverage for core Contacts and Companies flows."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio

from backend.models import Deal
from backend.tests.conftest import auth_header


@pytest_asyncio.fixture
async def coverage_deal(db_session, seeded_org, pipeline, stages):
    deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Coverage Child Deal",
        status="open",
        owner_id=seeded_org["alpha-rep"].id,
    )
    db_session.add(deal)
    await db_session.commit()
    return deal


@pytest.mark.asyncio
async def test_company_crud_list_and_archive(async_client, seeded_org):
    headers = auth_header(seeded_org["admin"])
    created = await async_client.post(
        "/api/v1/companies/",
        headers=headers,
        json={
            "name": "Coverage Holdings",
            "domain": "coverage.example",
            "industry": "Technology",
            "size_range": "51-200",
            "website": "https://coverage.example",
            "tags": ["coverage"],
            "custom_fields": {"source": "test"},
        },
    )
    assert created.status_code == 201, created.text
    company_id = created.json()["id"]

    listed = await async_client.get("/api/v1/companies/?search=Coverage&industry=Technology", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = await async_client.patch(
        f"/api/v1/companies/{company_id}",
        headers=headers,
        json={"website": "https://updated.example", "tags": ["updated"], "custom_fields": {"reviewed": True}},
    )
    assert updated.status_code == 200
    assert updated.json()["website"] == "https://updated.example"

    detail = await async_client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["linked_contacts_count"] == 0

    archived = await async_client.delete(f"/api/v1/companies/{company_id}", headers=headers)
    assert archived.status_code == 204
    assert (await async_client.get(f"/api/v1/companies/{company_id}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_contact_crud_list_and_archive(async_client, seeded_org):
    headers = auth_header(seeded_org["admin"])
    company = await async_client.post("/api/v1/companies/", headers=headers, json={"name": "Contact Coverage Co"})
    assert company.status_code == 201
    company_id = company.json()["id"]

    created = await async_client.post(
        "/api/v1/contacts/",
        headers=headers,
        json={"first_name": "Core", "last_name": "Coverage", "email": "core.coverage@example.com", "company_id": company_id, "tags": ["coverage"]},
    )
    assert created.status_code == 201, created.text
    contact_id = created.json()["id"]

    listed = await async_client.get("/api/v1/contacts/?search=Core&company_id=" + company_id, headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = await async_client.patch(
        f"/api/v1/contacts/{contact_id}", headers=headers,
        json={"title": "VP", "lifecycle_stage": "qualified", "custom_fields": {"reviewed": True}},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "VP"

    assert (await async_client.get(f"/api/v1/contacts/{contact_id}", headers=headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)).status_code == 204


@pytest.mark.asyncio
async def test_contact_related_activity_not_found_and_owner_guard(async_client, seeded_org):
    owner_headers = auth_header(seeded_org["alpha-rep"])
    other_headers = auth_header(seeded_org["beta-rep"])
    created = await async_client.post(
        "/api/v1/contacts/", headers=owner_headers,
        json={"first_name": "Related", "last_name": "Contact", "email": "related@example.com"},
    )
    assert created.status_code == 201
    contact_id = created.json()["id"]
    assert (await async_client.patch(f"/api/v1/contacts/{contact_id}", headers=other_headers, json={"title": "Denied"})).status_code == 403
    activity = await async_client.post(
        f"/api/v1/contacts/{contact_id}/activities", headers=owner_headers,
        json={"activity_type": "call", "notes": "Covered", "occurred_at": "2026-09-02T12:00:00Z"},
    )
    assert activity.status_code == 201
    assert len((await async_client.get(f"/api/v1/contacts/{contact_id}/activities?limit=1", headers=owner_headers)).json()) == 1
    assert (await async_client.get(f"/api/v1/contacts/{contact_id}/deals", headers=owner_headers)).status_code == 200
    assert (await async_client.get(f"/api/v1/contacts/{uuid4()}", headers=owner_headers)).status_code == 404


@pytest.mark.asyncio
async def test_company_related_not_found_and_owner_guard(async_client, seeded_org):
    owner_headers = auth_header(seeded_org["alpha-rep"])
    other_headers = auth_header(seeded_org["beta-rep"])
    created = await async_client.post("/api/v1/companies/", headers=owner_headers, json={"name": "Related Company"})
    assert created.status_code == 201
    company_id = created.json()["id"]
    contact = await async_client.post(
        "/api/v1/contacts/", headers=owner_headers,
        json={"first_name": "Company", "last_name": "Contact", "company_id": company_id},
    )
    assert contact.status_code == 201
    assert (await async_client.patch(f"/api/v1/companies/{company_id}", headers=other_headers, json={"industry": "Denied"})).status_code == 403
    contacts = await async_client.get(f"/api/v1/companies/{company_id}/contacts", headers=owner_headers)
    assert contacts.status_code == 200 and len(contacts.json()) == 1
    assert (await async_client.get(f"/api/v1/companies/{company_id}/deals", headers=owner_headers)).status_code == 200
    assert (await async_client.get(f"/api/v1/companies/{uuid4()}", headers=owner_headers)).status_code == 404


@pytest.mark.asyncio
async def test_deal_counterparty_and_funding_lifecycle(async_client, seeded_org, coverage_deal):
    headers = auth_header(seeded_org["alpha-rep"])
    deal_id = str(coverage_deal.id)
    provider = await async_client.post("/api/v1/companies/", headers=headers, json={"name": "Capital Provider"})
    assert provider.status_code == 201

    counterparty = await async_client.post(
        f"/api/v1/deals/{deal_id}/counterparties/", headers=headers,
        json={"company_id": provider.json()["id"], "next_steps": "Call"},
    )
    assert counterparty.status_code == 201, counterparty.text
    counterparty_id = counterparty.json()["id"]
    assert (await async_client.patch(
        f"/api/v1/deals/{deal_id}/counterparties/{counterparty_id}", headers=headers, json={"notes": "Updated"},
    )).status_code == 200
    assert (await async_client.get(f"/api/v1/deals/{deal_id}/counterparties/?page=1&size=1", headers=headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/deals/{deal_id}/counterparties/{counterparty_id}", headers=headers)).status_code == 204

    funding = await async_client.post(
        f"/api/v1/deals/{deal_id}/funding/", headers=headers,
        json={"capital_provider_id": provider.json()["id"], "projected_commitment_amount": 1000000, "terms": "Standard"},
    )
    assert funding.status_code == 201, funding.text
    funding_id = funding.json()["id"]
    assert (await async_client.patch(
        f"/api/v1/deals/{deal_id}/funding/{funding_id}", headers=headers, json={"comments_next_steps": "Follow up"},
    )).status_code == 200
    assert (await async_client.get(f"/api/v1/deals/{deal_id}/funding/?page=1&size=1", headers=headers)).status_code == 200
    assert (await async_client.delete(f"/api/v1/deals/{deal_id}/funding/{funding_id}", headers=headers)).status_code == 204


@pytest.mark.asyncio
async def test_deal_child_not_found_and_cross_team_denial(async_client, seeded_org, coverage_deal):
    beta_headers = auth_header(seeded_org["beta-rep"])
    alpha_deal_id = str(coverage_deal.id)
    assert (await async_client.get(f"/api/v1/deals/{uuid4()}/counterparties/", headers=beta_headers)).status_code in {403, 404}
    assert (await async_client.get(f"/api/v1/deals/{alpha_deal_id}/funding/", headers=beta_headers)).status_code == 403


@pytest.mark.asyncio
async def test_admin_lifecycle_and_error_paths(async_client, seeded_org):
    admin_headers = auth_header(seeded_org["admin"])
    member_headers = auth_header(seeded_org["alpha-rep"])
    assert (await async_client.get("/api/v1/admin/groups?include_inactive=true", headers=member_headers)).status_code == 403
    assert (await async_client.patch(f"/api/v1/admin/users/{uuid4()}", headers=admin_headers, json={"is_active": False})).status_code == 404
    assert (await async_client.post(
        "/api/v1/admin/users", headers=admin_headers,
        json={"full_name": "Duplicate", "email": "admin@example.com", "password": "password123"},
    )).status_code == 409
    assert (await async_client.post(
        "/api/v1/admin/users", headers=admin_headers,
        json={"full_name": "Invalid Team", "email": "invalid-team@example.com", "password": "password123", "team_id": str(uuid4())},
    )).status_code == 400
    group = await async_client.post("/api/v1/admin/groups", headers=admin_headers, json={"name": "Lifecycle Group"})
    assert group.status_code == 201
    group_id = group.json()["id"]
    deactivated = await async_client.patch(f"/api/v1/admin/groups/{group_id}", headers=admin_headers, json={"is_active": False})
    assert deactivated.status_code == 200 and deactivated.json()["is_active"] is False
    reactivated = await async_client.patch(f"/api/v1/admin/groups/{group_id}", headers=admin_headers, json={"is_active": True})
    assert reactivated.status_code == 200 and reactivated.json()["is_active"] is True
    assert (await async_client.patch(f"/api/v1/admin/groups/{uuid4()}", headers=admin_headers, json={"name": "Missing"})).status_code == 404
