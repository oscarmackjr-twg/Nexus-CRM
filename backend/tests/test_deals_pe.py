"""Tests for Deal PE field persistence, label resolution, and deal_team CRUD — DEAL-10"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.auth.security import create_access_token, hash_password
from backend.models import Organization, Pipeline, PipelineStage, RefData, Team, User


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def pe_seed(db_session):
    org = Organization(name="PEOrg", slug="peorg")
    db_session.add(org)
    await db_session.flush()

    team = Team(org_id=org.id, name="Deal Team", type="sales")
    db_session.add(team)
    await db_session.flush()

    manager = User(
        org_id=org.id,
        email="pe-manager@example.com",
        username="pe-manager",
        hashed_password=hash_password("secret123"),
        full_name="PE Manager",
        role="supervisor",
        team_id=team.id,
        is_active=True,
    )
    member = User(
        org_id=org.id,
        email="pe-member@example.com",
        username="pe-member",
        hashed_password=hash_password("secret123"),
        full_name="PE Member",
        role="regular_user",
        team_id=team.id,
        is_active=True,
    )
    db_session.add_all([manager, member])
    await db_session.flush()

    pipeline = Pipeline(
        org_id=org.id,
        team_id=team.id,
        name="PE Pipeline",
        created_by=manager.id,
    )
    db_session.add(pipeline)
    await db_session.flush()

    stage = PipelineStage(
        pipeline_id=pipeline.id,
        name="Sourcing",
        position=1,
        probability=10,
        stage_type="open",
    )
    db_session.add(stage)
    await db_session.flush()

    # Seed a transaction_type ref_data row
    txn_type_ref = RefData(
        org_id=None,
        category="transaction_type",
        value="equity",
        label="Equity",
        position=1,
        is_active=True,
    )
    db_session.add(txn_type_ref)
    await db_session.commit()

    return {
        "org": org,
        "team": team,
        "manager": manager,
        "member": member,
        "pipeline": pipeline,
        "stage": stage,
        "txn_type_ref": txn_type_ref,
    }


@pytest.mark.asyncio
async def test_deal_pe_fields_persist(client, pe_seed):
    """PATCH with PE scalar fields — they persist and GET returns them correctly."""
    headers = auth_header(pe_seed["manager"])
    pipeline_id = str(pe_seed["pipeline"].id)
    stage_id = str(pe_seed["stage"].id)

    # Create a deal
    create_resp = await client.post(
        "/api/v1/deals",
        json={
            "name": "PE Test Deal",
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "value": 0,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    # PATCH with PE scalar fields
    patch_resp = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={
            "description": "A flagship equity raise",
            "new_deal_date": "2025-01-15",
            "revenue_amount": 1000000.0,
            "revenue_currency": "USD",
            "ebitda_amount": 250000.0,
            "ebitda_currency": "USD",
            "cim_received_date": "2025-02-01",
            "passed_dead_commentary": "Valuation too high",
        },
        headers=headers,
    )
    assert patch_resp.status_code == 200

    # GET the deal and assert all PE fields are present
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()

    assert data["description"] == "A flagship equity raise"
    assert data["new_deal_date"] == "2025-01-15"
    assert data["revenue_amount"] == 1000000.0
    assert data["revenue_currency"] == "USD"
    assert data["ebitda_amount"] == 250000.0
    assert data["ebitda_currency"] == "USD"
    assert data["cim_received_date"] == "2025-02-01"
    assert data["passed_dead_commentary"] == "Valuation too high"


@pytest.mark.asyncio
async def test_deal_labels_resolved(client, pe_seed):
    """PATCH with transaction_type_id — GET returns transaction_type_label resolved from ref_data."""
    headers = auth_header(pe_seed["manager"])
    pipeline_id = str(pe_seed["pipeline"].id)
    stage_id = str(pe_seed["stage"].id)
    # Use hex format (no hyphens) to match how SQLite stores UUID primary keys
    # In PostgreSQL, both formats work; in SQLite we need the raw hex form for FK joins
    txn_type_id = pe_seed["txn_type_ref"].id.hex

    # Create a deal
    create_resp = await client.post(
        "/api/v1/deals",
        json={
            "name": "Label Resolution Deal",
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    # PATCH with transaction_type_id
    patch_resp = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={"transaction_type_id": txn_type_id},
        headers=headers,
    )
    assert patch_resp.status_code == 200

    # GET and assert label resolved
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()

    assert data["transaction_type_id"] is not None
    assert data["transaction_type_label"] == "Equity"


@pytest.mark.asyncio
async def test_deal_team_crud(client, pe_seed):
    """PATCH with deal_team_ids — GET returns deal_team with user details."""
    headers = auth_header(pe_seed["manager"])
    pipeline_id = str(pe_seed["pipeline"].id)
    stage_id = str(pe_seed["stage"].id)
    member_id = pe_seed["member"].id.hex  # hex matches SQLite storage; response returns str(UUID) with hyphens
    member_id_str = str(pe_seed["member"].id)  # hyphenated form, returned by _load_deal_team

    # Create a deal
    create_resp = await client.post(
        "/api/v1/deals",
        json={
            "name": "Team Deal",
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    # Initially deal_team should be empty
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.json()["deal_team"] == []

    # PATCH deal_team_ids to assign the member
    patch_resp = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={"deal_team_ids": [member_id]},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    # The PATCH response itself should include deal_team (returned from get_deal)
    assert len(patch_data["deal_team"]) == 1, f"PATCH response deal_team: {patch_data['deal_team']}"

    # GET and assert deal_team contains the member
    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data["deal_team"]) == 1
    # _load_deal_team returns str(row.id) which SQLAlchemy converts to hyphenated UUID str
    assert data["deal_team"][0]["id"] == member_id_str
    assert data["deal_team"][0]["name"] == "PE Member"

    # PATCH with empty list to clear team
    patch_resp2 = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={"deal_team_ids": []},
        headers=headers,
    )
    assert patch_resp2.status_code == 200

    get_resp2 = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp2.json()["deal_team"] == []


@pytest.mark.asyncio
async def test_existing_deals_backward_compatible(client, pe_seed):
    """Existing deals return safely with null/empty defaults for all new PE fields."""
    headers = auth_header(pe_seed["manager"])
    pipeline_id = str(pe_seed["pipeline"].id)
    stage_id = str(pe_seed["stage"].id)

    create_resp = await client.post(
        "/api/v1/deals",
        json={"name": "Legacy Deal", "pipeline_id": pipeline_id, "stage_id": stage_id},
        headers=headers,
    )
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/deals/{deal_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()

    # All new PE fields default to None or empty
    assert data["transaction_type_id"] is None
    assert data["transaction_type_label"] is None
    assert data["fund_id"] is None
    assert data["fund_name"] is None
    assert data["revenue_amount"] is None
    assert data["passed_dead_reasons"] == []
    assert data["deal_team"] == []
