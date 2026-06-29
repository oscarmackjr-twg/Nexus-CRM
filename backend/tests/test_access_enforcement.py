"""
Integration tests for access enforcement — list/visibility/global-read matrix.

Covers:
  ACCESS-01: Contacts and Companies globally readable regardless of group
  ACCESS-02: Deal list scoping — regular_user and supervisor see own team only (silent filter, never 403)
  ACCESS-05: Principal reads all deals across all groups

Decisions enforced:
  D-03: LIST endpoints silently filter — never return 403
  D-06: Principal read-all
  D-11: is_private oversight-role exemption
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from backend.models import Deal
from backend.tests.conftest import auth_header


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def deal_fixtures(db_session, seeded_org, pipeline, stages):
    """
    Seed three deals for the cross-group list/visibility matrix:
      alpha_deal    — alpha team, owner alpha-rep,  public
      beta_deal     — beta team,  owner beta-rep,   public
      alpha_private — alpha team, owner alpha-peer, is_private=True
    """
    alpha_deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Alpha Deal",
        value=1000,
        probability=25,
        status="open",
        owner_id=seeded_org["alpha-rep"].id,
    )
    beta_deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["beta"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Beta Deal",
        value=2000,
        probability=30,
        status="open",
        owner_id=seeded_org["beta-rep"].id,
    )
    alpha_private = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Alpha Private Deal",
        value=1500,
        probability=50,
        status="open",
        owner_id=seeded_org["alpha-peer"].id,
        is_private=True,
    )
    db_session.add_all([alpha_deal, beta_deal, alpha_private])
    await db_session.commit()
    return {
        "alpha_deal": alpha_deal,
        "beta_deal": beta_deal,
        "alpha_private": alpha_private,
    }


def _deal_names(response_json) -> set[str]:
    """Extract deal names from a list endpoint response."""
    return {item["name"] for item in response_json["items"]}


# ── List scoping tests (D-03: no 403 on LIST ever) ───────────────────────────

@pytest.mark.asyncio
async def test_admin_sees_all_teams_in_list(async_client, seeded_org, deal_fixtures):
    """Admin GET /api/v1/deals returns both alpha and beta team deals (ACCESS-06 cross-group)."""
    admin = seeded_org["admin"]
    response = await async_client.get("/api/v1/deals", headers=auth_header(admin))
    assert response.status_code == 200, response.text
    names = _deal_names(response.json())
    assert "Alpha Deal" in names, "Admin must see alpha deals"
    assert "Beta Deal" in names, "Admin must see beta deals"


@pytest.mark.asyncio
async def test_principal_sees_all_teams_in_list(async_client, seeded_org, deal_fixtures):
    """Principal GET /api/v1/deals returns both alpha and beta deals (ACCESS-05 read-all)."""
    principal = seeded_org["principal"]
    response = await async_client.get("/api/v1/deals", headers=auth_header(principal))
    assert response.status_code == 200, response.text
    names = _deal_names(response.json())
    assert "Alpha Deal" in names, "Principal must see alpha deals"
    assert "Beta Deal" in names, "Principal must see beta deals"


@pytest.mark.asyncio
async def test_beta_rep_sees_only_beta_deals(async_client, seeded_org, deal_fixtures):
    """beta-rep GET /api/v1/deals returns ONLY beta deals — alpha deals absent (ACCESS-02 silent filter, D-03 no 403)."""
    beta_rep = seeded_org["beta-rep"]
    response = await async_client.get("/api/v1/deals", headers=auth_header(beta_rep))
    assert response.status_code == 200, response.text  # D-03: LIST never returns 403
    names = _deal_names(response.json())
    assert "Beta Deal" in names, "beta-rep must see own team deal"
    assert "Alpha Deal" not in names, "beta-rep must NOT see alpha team deal"
    assert "Alpha Private Deal" not in names, "beta-rep must NOT see alpha team private deal"


@pytest.mark.asyncio
async def test_supervisor_sees_private_deal_from_teammate(async_client, seeded_org, deal_fixtures):
    """alpha-manager (supervisor) GET /api/v1/deals sees is_private deal owned by alpha-peer (D-11 oversight exemption)."""
    alpha_manager = seeded_org["alpha-manager"]
    response = await async_client.get("/api/v1/deals", headers=auth_header(alpha_manager))
    assert response.status_code == 200, response.text
    names = _deal_names(response.json())
    assert "Alpha Private Deal" in names, "Supervisor must see same-team private deal (D-11)"


@pytest.mark.asyncio
async def test_regular_user_does_not_see_private_deal_from_teammate(async_client, seeded_org, deal_fixtures):
    """alpha-rep (regular_user, NOT the owner) does NOT see the alpha-peer's is_private deal (D-11)."""
    alpha_rep = seeded_org["alpha-rep"]
    response = await async_client.get("/api/v1/deals", headers=auth_header(alpha_rep))
    assert response.status_code == 200, response.text
    names = _deal_names(response.json())
    assert "Alpha Deal" in names, "alpha-rep must see own deal"
    assert "Alpha Private Deal" not in names, "regular_user non-owner must NOT see private deal"


@pytest.mark.asyncio
async def test_list_endpoints_never_return_403(async_client, seeded_org, deal_fixtures):
    """D-03: LIST endpoints return 200 for every role, even when their result set is empty."""
    for username in ("alpha-rep", "beta-rep", "alpha-manager", "beta-manager"):
        user = seeded_org[username]
        response = await async_client.get("/api/v1/deals", headers=auth_header(user))
        assert response.status_code == 200, (
            f"{username} GET /api/v1/deals must return 200, not {response.status_code}"
        )


# ── Global-read tests for Contacts / Companies (ACCESS-01, D-17) ─────────────

@pytest.mark.asyncio
async def test_contacts_globally_readable(async_client, seeded_org):
    """Every role GET /api/v1/contacts and GET /api/v1/companies returns 200 (ACCESS-01)."""
    users_to_check = ["admin", "principal", "alpha-manager", "alpha-rep", "beta-rep"]
    for username in users_to_check:
        user = seeded_org[username]
        contacts_resp = await async_client.get("/api/v1/contacts", headers=auth_header(user))
        assert contacts_resp.status_code == 200, (
            f"{username} GET /api/v1/contacts must return 200, got {contacts_resp.status_code}"
        )
        companies_resp = await async_client.get("/api/v1/companies", headers=auth_header(user))
        assert companies_resp.status_code == 200, (
            f"{username} GET /api/v1/companies must return 200, got {companies_resp.status_code}"
        )


# ── 403-vs-404 split for GET /api/v1/deals/{id} (ACCESS-07, D-01/D-02) ──────

@pytest.mark.asyncio
async def test_cross_team_deal_get_returns_403(async_client, seeded_org, deal_fixtures):
    """GET /api/v1/deals/{id} for an existing out-of-scope deal returns 403, not 404 (D-01/D-02, ACCESS-07)."""
    beta_deal_id = str(deal_fixtures["beta_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.get(f"/api/v1/deals/{beta_deal_id}", headers=auth_header(alpha_rep))
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_nonexistent_deal_get_returns_404(async_client, seeded_org):
    """GET /api/v1/deals/{random-uuid} returns 404 when deal does not exist (D-02)."""
    import uuid
    fake_id = str(uuid.uuid4())
    admin = seeded_org["admin"]
    resp = await async_client.get(f"/api/v1/deals/{fake_id}", headers=auth_header(admin))
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


@pytest.mark.asyncio
async def test_own_deal_get_returns_200(async_client, seeded_org, deal_fixtures):
    """GET /api/v1/deals/{id} for own deal returns 200 with response body."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.get(f"/api/v1/deals/{alpha_deal_id}", headers=auth_header(alpha_rep))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json()["id"] == alpha_deal_id


@pytest.mark.asyncio
async def test_private_deal_regular_user_nonowner_returns_403(async_client, seeded_org, deal_fixtures):
    """Regular user reading a private deal they don't own (same team) returns 403 (D-11)."""
    private_deal_id = str(deal_fixtures["alpha_private"].id)
    alpha_rep = seeded_org["alpha-rep"]  # NOT the owner; alpha-peer owns it
    resp = await async_client.get(f"/api/v1/deals/{private_deal_id}", headers=auth_header(alpha_rep))
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_private_deal_supervisor_same_team_returns_200(async_client, seeded_org, deal_fixtures):
    """Supervisor reading a private deal from same team returns 200 (D-11 oversight exemption)."""
    private_deal_id = str(deal_fixtures["alpha_private"].id)
    alpha_manager = seeded_org["alpha-manager"]
    resp = await async_client.get(f"/api/v1/deals/{private_deal_id}", headers=auth_header(alpha_manager))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_activities_cross_team_returns_403(async_client, seeded_org, deal_fixtures):
    """GET /api/v1/deals/{id}/activities for out-of-scope deal returns 403 (Bug 9, D-01, D-19)."""
    beta_deal_id = str(deal_fixtures["beta_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.get(
        f"/api/v1/deals/{beta_deal_id}/activities",
        headers=auth_header(alpha_rep),
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


# ── Write/delete guard matrix (ACCESS-03, ACCESS-04, ACCESS-06, D-07, D-08, D-13) ─

@pytest.mark.asyncio
async def test_regular_user_update_own_deal_returns_200(async_client, seeded_org, deal_fixtures):
    """Regular User updating own deal returns 200 (ACCESS-03)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]  # owner of alpha_deal
    resp = await async_client.put(
        f"/api/v1/deals/{alpha_deal_id}",
        headers=auth_header(alpha_rep),
        json={"name": "Updated Alpha Deal"},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_regular_user_update_team_member_deal_returns_403(async_client, seeded_org, deal_fixtures):
    """Regular User updating a same-team member's deal (not own) returns 403 (ACCESS-03)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_peer = seeded_org["alpha-peer"]  # same team as alpha-rep but NOT the owner
    resp = await async_client.put(
        f"/api/v1/deals/{alpha_deal_id}",
        headers=auth_header(alpha_peer),
        json={"name": "Peer Tries to Edit"},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_supervisor_update_same_team_deal_returns_200(async_client, seeded_org, deal_fixtures):
    """Supervisor updating a same-team member's deal returns 200 (ACCESS-04)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]
    resp = await async_client.put(
        f"/api/v1/deals/{alpha_deal_id}",
        headers=auth_header(alpha_manager),
        json={"name": "Manager Updated Alpha Deal"},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_supervisor_update_cross_team_deal_returns_403(async_client, seeded_org, deal_fixtures):
    """Supervisor updating another team's deal returns 403 (Bug 4 fix, ACCESS-04)."""
    beta_deal_id = str(deal_fixtures["beta_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]
    resp = await async_client.put(
        f"/api/v1/deals/{beta_deal_id}",
        headers=auth_header(alpha_manager),
        json={"name": "Supervisor Cross-Team Edit"},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_supervisor_move_stage_same_team_returns_200(async_client, seeded_org, deal_fixtures, stages):
    """Supervisor moving stage on same-team deal returns 200 (ACCESS-04)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]
    resp = await async_client.post(
        f"/api/v1/deals/{alpha_deal_id}/move-stage",
        headers=auth_header(alpha_manager),
        json={"stage_id": str(stages[1].id), "log_activity": False},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_supervisor_move_stage_cross_team_returns_403(async_client, seeded_org, deal_fixtures, stages):
    """Supervisor moving stage on cross-team deal returns 403 (Bug 6 fix, ACCESS-04)."""
    beta_deal_id = str(deal_fixtures["beta_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]
    resp = await async_client.post(
        f"/api/v1/deals/{beta_deal_id}/move-stage",
        headers=auth_header(alpha_manager),
        json={"stage_id": str(stages[1].id), "log_activity": False},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_nonadmin_owner_id_change_returns_403(async_client, seeded_org, deal_fixtures):
    """Non-admin (supervisor) supplying owner_id in update returns 403 (D-13, Bug 5 fix)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]  # supervisor, not admin
    alpha_peer = seeded_org["alpha-peer"]
    resp = await async_client.put(
        f"/api/v1/deals/{alpha_deal_id}",
        headers=auth_header(alpha_manager),
        json={"owner_id": str(alpha_peer.id)},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_owner_delete_own_deal_returns_204(async_client, seeded_org, deal_fixtures):
    """Owner deleting their own deal returns 204 (D-07)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]  # owner of alpha_deal
    resp = await async_client.delete(f"/api/v1/deals/{alpha_deal_id}", headers=auth_header(alpha_rep))
    assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_supervisor_delete_team_member_deal_returns_403(async_client, seeded_org, deal_fixtures):
    """Supervisor deleting a same-team member's deal returns 403 (D-08, ACCESS-04)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_manager = seeded_org["alpha-manager"]  # NOT the owner (alpha-rep is)
    resp = await async_client.delete(f"/api/v1/deals/{alpha_deal_id}", headers=auth_header(alpha_manager))
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


# ── Admin full-CRUD + CREATE team_id forcing (ACCESS-06, D-09, D-12) ─────────

@pytest.mark.asyncio
async def test_admin_update_both_team_deals_returns_200(async_client, seeded_org, deal_fixtures):
    """Admin updating deals in both alpha and beta teams returns 200 — never 403 (ACCESS-06, D-09)."""
    admin = seeded_org["admin"]

    resp_alpha = await async_client.put(
        f"/api/v1/deals/{deal_fixtures['alpha_deal'].id}",
        headers=auth_header(admin),
        json={"name": "Admin Updated Alpha"},
    )
    assert resp_alpha.status_code == 200, f"Admin update alpha: expected 200, got {resp_alpha.status_code}: {resp_alpha.text}"

    resp_beta = await async_client.put(
        f"/api/v1/deals/{deal_fixtures['beta_deal'].id}",
        headers=auth_header(admin),
        json={"name": "Admin Updated Beta"},
    )
    assert resp_beta.status_code == 200, f"Admin update beta: expected 200, got {resp_beta.status_code}: {resp_beta.text}"


@pytest.mark.asyncio
async def test_admin_move_stage_both_team_deals_returns_200(async_client, seeded_org, deal_fixtures, stages):
    """Admin moving stage on deals in both alpha and beta teams returns 200 (ACCESS-06, D-09)."""
    admin = seeded_org["admin"]

    resp_alpha = await async_client.post(
        f"/api/v1/deals/{deal_fixtures['alpha_deal'].id}/move-stage",
        headers=auth_header(admin),
        json={"stage_id": str(stages[1].id), "log_activity": False},
    )
    assert resp_alpha.status_code == 200, f"Admin move-stage alpha: expected 200, got {resp_alpha.status_code}: {resp_alpha.text}"

    resp_beta = await async_client.post(
        f"/api/v1/deals/{deal_fixtures['beta_deal'].id}/move-stage",
        headers=auth_header(admin),
        json={"stage_id": str(stages[1].id), "log_activity": False},
    )
    assert resp_beta.status_code == 200, f"Admin move-stage beta: expected 200, got {resp_beta.status_code}: {resp_beta.text}"


@pytest.mark.asyncio
async def test_admin_delete_cross_team_deal_returns_204(async_client, seeded_org, deal_fixtures):
    """Admin deleting a cross-team deal returns 204 (ACCESS-06, D-09)."""
    admin = seeded_org["admin"]
    beta_deal_id = str(deal_fixtures["beta_deal"].id)
    resp = await async_client.delete(f"/api/v1/deals/{beta_deal_id}", headers=auth_header(admin))
    assert resp.status_code == 204, f"Admin delete beta deal: expected 204, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_admin_owner_id_change_returns_200(async_client, seeded_org, deal_fixtures):
    """Admin reassigning owner_id returns 200 (D-13 — admin-only override)."""
    admin = seeded_org["admin"]
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_peer = seeded_org["alpha-peer"]  # same alpha team, different user
    resp = await async_client.put(
        f"/api/v1/deals/{alpha_deal_id}",
        headers=auth_header(admin),
        json={"owner_id": str(alpha_peer.id)},
    )
    assert resp.status_code == 200, f"Admin owner_id reassign: expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json()["owner_id"] == str(alpha_peer.id), "owner_id must be updated to alpha_peer"


@pytest.mark.asyncio
async def test_create_deal_forces_creator_team_id(async_client, seeded_org, pipeline, stages):
    """Created deal's team_id equals creator's team_id, not any payload value (D-12)."""
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.post(
        "/api/v1/deals",
        headers=auth_header(alpha_rep),
        json={
            "name": "Team ID Forced Deal",
            "pipeline_id": str(pipeline.id),
            "stage_id": str(stages[0].id),
        },
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    assert resp.json()["team_id"] == str(seeded_org["alpha"].id), (
        f"team_id must equal creator's team (alpha), got {resp.json()['team_id']}"
    )


@pytest.mark.asyncio
async def test_create_deal_principal_forces_own_team_id(async_client, seeded_org, pipeline, stages):
    """Principal creating a deal gets team_id == principal's own team_id (D-06/D-12)."""
    principal = seeded_org["principal"]  # in alpha team
    resp = await async_client.post(
        "/api/v1/deals",
        headers=auth_header(principal),
        json={
            "name": "Principal Created Deal",
            "pipeline_id": str(pipeline.id),
            "stage_id": str(stages[0].id),
        },
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    assert resp.json()["team_id"] == str(seeded_org["alpha"].id), (
        f"principal deal team_id must equal principal's team (alpha), got {resp.json()['team_id']}"
    )


# ── Deal child entity scope tests (D-19, ACCESS-02/07 via child endpoints) ─────

@pytest.mark.asyncio
async def test_cross_team_counterparties_list_returns_403(async_client, seeded_org, deal_fixtures):
    """beta-rep GET /counterparties on alpha deal returns 403 — cannot read parent (D-19, ACCESS-02)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    beta_rep = seeded_org["beta-rep"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/counterparties/",
        headers=auth_header(beta_rep),
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_cross_team_counterparties_create_returns_403(async_client, seeded_org, deal_fixtures):
    """beta-rep POST /counterparties on alpha deal returns 403 — IDOR side-door closed (D-19, T-18-10)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    beta_rep = seeded_org["beta-rep"]
    # company_id is required by DealCounterpartyCreate; a dummy UUID is fine —
    # the 403 is raised by require_deal_writable before any DB insert.
    resp = await async_client.post(
        f"/api/v1/deals/{alpha_deal_id}/counterparties/",
        headers=auth_header(beta_rep),
        json={"company_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_cross_team_funding_list_returns_403(async_client, seeded_org, deal_fixtures):
    """beta-rep GET /funding on alpha deal returns 403 — cannot read parent (D-19, ACCESS-02)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    beta_rep = seeded_org["beta-rep"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/funding/",
        headers=auth_header(beta_rep),
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_cross_team_funding_create_returns_403(async_client, seeded_org, deal_fixtures):
    """beta-rep POST /funding on alpha deal returns 403 — IDOR side-door closed (D-19, T-18-11)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    beta_rep = seeded_org["beta-rep"]
    resp = await async_client.post(
        f"/api/v1/deals/{alpha_deal_id}/funding/",
        headers=auth_header(beta_rep),
        json={},
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_own_team_counterparties_list_returns_200(async_client, seeded_org, deal_fixtures):
    """alpha-rep GET /counterparties on own team deal returns 200 (D-19 positive path)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/counterparties/",
        headers=auth_header(alpha_rep),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_admin_counterparties_list_cross_team_returns_200(async_client, seeded_org, deal_fixtures):
    """Admin GET /counterparties on any team deal returns 200 (ACCESS-06, D-09)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    admin = seeded_org["admin"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/counterparties/",
        headers=auth_header(admin),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_own_team_funding_list_returns_200(async_client, seeded_org, deal_fixtures):
    """alpha-rep GET /funding on own team deal returns 200 (D-19 positive path)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    alpha_rep = seeded_org["alpha-rep"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/funding/",
        headers=auth_header(alpha_rep),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_admin_funding_list_cross_team_returns_200(async_client, seeded_org, deal_fixtures):
    """Admin GET /funding on any team deal returns 200 (ACCESS-06, D-09)."""
    alpha_deal_id = str(deal_fixtures["alpha_deal"].id)
    admin = seeded_org["admin"]
    resp = await async_client.get(
        f"/api/v1/deals/{alpha_deal_id}/funding/",
        headers=auth_header(admin),
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
