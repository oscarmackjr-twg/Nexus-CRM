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
