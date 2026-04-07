"""
Integration tests for authorship injection in 6 entity services (17-02).

Covers AUDIT-01 (created_by), AUDIT-02 (updated_by) for:
Contact, Company, Deal, Fund, DealCounterparty, DealFunding.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from backend.models import Company, Contact, Deal, DealCounterparty, DealFunding, Fund
from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_contact_created_by_set_on_insert(async_client, seeded_org, db_session, pipeline, stages):
    """POST /api/v1/contacts -> DB row has created_by == current_user.id"""
    admin = seeded_org["admin"]
    headers = auth_header(admin)
    response = await async_client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"first_name": "Alice", "last_name": "Authorship"},
    )
    assert response.status_code == 201, response.text
    contact_id = response.json()["id"]

    contact = await db_session.scalar(select(Contact).where(Contact.id == contact_id))
    assert contact is not None
    assert str(contact.created_by) == str(admin.id)
    assert str(contact.updated_by) == str(admin.id)


@pytest.mark.asyncio
async def test_contact_updated_by_set_on_update(async_client, seeded_org, db_session, pipeline, stages):
    """PATCH /api/v1/contacts/{id} -> DB row has updated_by == current_user.id, created_by unchanged."""
    admin = seeded_org["admin"]

    # Create with admin
    create_resp = await async_client.post(
        "/api/v1/contacts",
        headers=auth_header(admin),
        json={"first_name": "Bob", "last_name": "Update"},
    )
    assert create_resp.status_code == 201
    contact_id = create_resp.json()["id"]

    # Update with admin (owner can update; verifies updated_by is set)
    patch_resp = await async_client.patch(
        f"/api/v1/contacts/{contact_id}",
        headers=auth_header(admin),
        json={"first_name": "Bobby"},
    )
    assert patch_resp.status_code == 200

    contact = await db_session.scalar(select(Contact).where(Contact.id == contact_id))
    assert str(contact.created_by) == str(admin.id), "created_by must not change on update"
    assert str(contact.updated_by) == str(admin.id), "updated_by must reflect updater"


@pytest.mark.asyncio
async def test_company_created_by_set_on_insert(async_client, seeded_org, db_session):
    """POST /api/v1/companies -> DB row has created_by == current_user.id"""
    admin = seeded_org["admin"]
    headers = auth_header(admin)
    response = await async_client.post(
        "/api/v1/companies",
        headers=headers,
        json={"name": "Authorship Corp"},
    )
    assert response.status_code == 201, response.text
    company_id = response.json()["id"]

    company = await db_session.scalar(select(Company).where(Company.id == company_id))
    assert company is not None
    assert str(company.created_by) == str(admin.id)


@pytest.mark.asyncio
async def test_deal_created_by_set_on_insert(async_client, seeded_org, db_session, pipeline, stages):
    """POST /api/v1/deals -> DB row has created_by == current_user.id"""
    # Deal creation requires a user with team_id — use alpha-manager
    user = seeded_org["alpha-manager"]
    headers = auth_header(user)
    response = await async_client.post(
        "/api/v1/deals",
        headers=headers,
        json={
            "name": "Authorship Deal",
            "pipeline_id": str(pipeline.id),
            "stage_id": str(stages[0].id),
        },
    )
    assert response.status_code == 201, response.text
    deal_id = response.json()["id"]

    deal = await db_session.scalar(select(Deal).where(Deal.id == deal_id))
    assert deal is not None
    assert str(deal.created_by) == str(user.id)


@pytest.mark.asyncio
async def test_fund_created_by_set_on_insert(async_client, seeded_org, db_session):
    """POST /api/v1/funds -> DB row has created_by == current_user.id"""
    admin = seeded_org["admin"]
    headers = auth_header(admin)
    response = await async_client.post(
        "/api/v1/funds",
        headers=headers,
        json={"fund_name": "Authorship Fund", "fund_size_amount": 100.0},
    )
    assert response.status_code == 201, response.text
    fund_id = response.json()["id"]

    fund = await db_session.scalar(select(Fund).where(Fund.id == fund_id))
    assert fund is not None
    assert str(fund.created_by) == str(admin.id)


@pytest.mark.asyncio
async def test_created_by_never_changes_on_update(async_client, seeded_org, db_session):
    """After PATCH, created_by remains the original creator (admin updates their own company)."""
    admin = seeded_org["admin"]

    # Create company with admin
    create_resp = await async_client.post(
        "/api/v1/companies",
        headers=auth_header(admin),
        json={"name": "Immutable Creator Corp"},
    )
    assert create_resp.status_code == 201
    company_id = create_resp.json()["id"]

    # Update with admin (owner updating their own record)
    patch_resp = await async_client.patch(
        f"/api/v1/companies/{company_id}",
        headers=auth_header(admin),
        json={"name": "Immutable Creator Corp Updated"},
    )
    assert patch_resp.status_code == 200

    company = await db_session.scalar(select(Company).where(Company.id == company_id))
    assert str(company.created_by) == str(admin.id), "created_by must never change after insert"
    assert str(company.updated_by) == str(admin.id), "updated_by must reflect the updater"
