from __future__ import annotations

import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, event, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_nexus.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test_nexus.db")

from backend.api.main import app
from backend.auth.security import create_access_token, encrypt_linkedin_token, hash_password
from backend.database import Base, get_engine, get_session_maker
from backend.models import Deal, DealActivity, Organization, Pipeline, PipelineStage, Team, User


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, tuple[str, float | None]] = {}
        self.sorted_sets: dict[str, dict[str, float]] = defaultdict(dict)

    def _purge_expired(self) -> None:
        now = time.time()
        for key, (_, expires_at) in list(self.store.items()):
            if expires_at is not None and expires_at <= now:
                self.store.pop(key, None)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        expires_at = time.time() + ex if ex else None
        self.store[key] = (value, expires_at)
        return True

    async def get(self, key: str) -> str | None:
        self._purge_expired()
        item = self.store.get(key)
        return item[0] if item else None

    async def delete(self, key: str) -> int:
        existed = key in self.store or key in self.sorted_sets
        self.store.pop(key, None)
        self.sorted_sets.pop(key, None)
        return int(existed)

    async def exists(self, key: str) -> int:
        self._purge_expired()
        return int(key in self.store or key in self.sorted_sets)

    async def ping(self) -> bool:
        return True

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self.store:
            value, _ = self.store[key]
            self.store[key] = (value, time.time() + seconds)
        return True

    async def zadd(self, key: str, mapping: dict[str, int | float]) -> int:
        self.sorted_sets[key].update({member: float(score) for member, score in mapping.items()})
        return len(mapping)

    async def zcard(self, key: str) -> int:
        return len(self.sorted_sets.get(key, {}))

    async def zremrangebyscore(self, key: str, minimum: int | float, maximum: int | float) -> int:
        bucket = self.sorted_sets.get(key, {})
        doomed = [member for member, score in bucket.items() if float(minimum) <= score <= float(maximum)]
        for member in doomed:
            bucket.pop(member, None)
        return len(doomed)

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False):
        bucket = sorted(self.sorted_sets.get(key, {}).items(), key=lambda item: item[1])
        if stop == -1:
            sliced = bucket[start:]
        else:
            sliced = bucket[start : stop + 1]
        if withscores:
            return sliced
        return [member for member, _ in sliced]

    async def lpush(self, key: str, *values: str) -> int:
        current, _ = self.store.get(key, ("[]", None))
        items = list(eval(current)) if isinstance(current, str) and current.startswith("[") else []
        items = list(values) + items
        self.store[key] = (repr(items), None)
        return len(items)

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        current = await self.get(key)
        items = list(eval(current)) if current else []
        self.store[key] = (repr(items[start : stop + 1]), None)
        return True

    async def aclose(self) -> None:
        return None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    session_factory = get_session_maker()
    async with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
    yield


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    client = FakeRedis()
    monkeypatch.setattr("backend.api.main.redis_async.from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr("backend.api.routes.auth.redis_async.from_url", lambda *args, **kwargs: client)
    return client


@pytest_asyncio.fixture
async def async_client(monkeypatch, fake_redis):
    async def fake_check_storage() -> None:
        return None

    monkeypatch.setattr("backend.api.main.check_storage", fake_check_storage)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=True) as ac:
        yield ac


@pytest_asyncio.fixture
async def client(async_client):
    yield async_client


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    session_factory = get_session_maker()
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_org(db_session):
    org = Organization(name="Acme", slug="acme")
    db_session.add(org)
    await db_session.flush()

    alpha = Team(org_id=org.id, name="Alpha", type="sales")
    beta = Team(org_id=org.id, name="Beta", type="sales")
    db_session.add_all([alpha, beta])
    await db_session.flush()

    users = {}
    for email, username, role, team in [
        ("super@example.com", "super", "admin", alpha),
        ("admin@example.com", "admin", "admin", alpha),
        ("alpha-manager@example.com", "alpha-manager", "supervisor", alpha),
        ("alpha-rep@example.com", "alpha-rep", "regular_user", alpha),
        ("alpha-peer@example.com", "alpha-peer", "regular_user", alpha),
        ("beta-manager@example.com", "beta-manager", "supervisor", beta),
        ("beta-rep@example.com", "beta-rep", "regular_user", beta),
        ("viewer@example.com", "viewer", "regular_user", alpha),
    ]:
        user = User(
            org_id=org.id,
            email=email,
            username=username,
            hashed_password=hash_password("secret123"),
            full_name=username.title(),
            role=role,
            team_id=team.id if team else None,
            is_active=True,
        )
        db_session.add(user)
        users[username] = user

    await db_session.commit()
    return {"org": org, "alpha": alpha, "beta": beta, **users}


@pytest.fixture
def admin_token(seeded_org):
    return auth_header(seeded_org["admin"])["Authorization"].split()[1]


@pytest.fixture
def rep_token(seeded_org):
    return auth_header(seeded_org["alpha-rep"])["Authorization"].split()[1]


@pytest_asyncio.fixture
async def multi_team_fixture(seeded_org):
    return seeded_org


@pytest.fixture
def auth_tokens():
    return {"access_token": "test-access", "refresh_token": "test-refresh", "token_type": "bearer"}


@pytest.fixture
def mock_linkedin(monkeypatch):
    class MockLinkedIn:
        async def search_people(self, **kwargs):
            return []

        async def get_person_profile(self, linkedin_member_id: str):
            from backend.schemas.linkedin import LinkedInPersonResult

            return LinkedInPersonResult(
                linkedin_member_id=linkedin_member_id,
                first_name="Morgan",
                last_name="Lee",
                headline="VP Sales",
                profile_url="https://linkedin.test/morgan",
                company_name="LinkedIn Co",
            )

        async def get_company(self, linkedin_company_id: str):
            from backend.schemas.linkedin import LinkedInCompanyResult

            return LinkedInCompanyResult(
                linkedin_company_id=linkedin_company_id,
                name="LinkedIn Co",
                industry="SaaS",
                website="https://linkedin-co.test",
                follower_count=10,
            )

        async def send_message(self, recipient_linkedin_id: str, message_text: str):
            return {"message_id": "msg-123", "sent_at": datetime.now(timezone.utc)}

    monkeypatch.setattr("backend.api.routes.linkedin._client", lambda current_user: MockLinkedIn())
    return MockLinkedIn()


@pytest_asyncio.fixture
async def pipeline(db_session, seeded_org):
    pipeline = Pipeline(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        name="Sales Pipeline",
        created_by=seeded_org["alpha-manager"].id,
    )
    db_session.add(pipeline)
    await db_session.flush()
    return pipeline


@pytest_asyncio.fixture
async def stages(db_session, pipeline):
    items = [
        PipelineStage(pipeline_id=pipeline.id, name="Lead", position=1, probability=10, stage_type="open"),
        PipelineStage(pipeline_id=pipeline.id, name="Qualified", position=2, probability=30, stage_type="open"),
        PipelineStage(pipeline_id=pipeline.id, name="Proposal Sent", position=3, probability=70, stage_type="open"),
        PipelineStage(pipeline_id=pipeline.id, name="Won", position=4, probability=100, stage_type="won"),
    ]
    db_session.add_all(items)
    await db_session.commit()
    return items


@pytest_asyncio.fixture
async def seed_50_deals(db_session, seeded_org, pipeline, stages):
    for index in range(50):
        db_session.add(
            Deal(
                org_id=seeded_org["org"].id,
                team_id=seeded_org["alpha"].id,
                pipeline_id=pipeline.id,
                stage_id=stages[index % len(stages)].id,
                name=f"Deal {index}",
                value=1000 + index,
                probability=25,
                status="open",
                owner_id=seeded_org["alpha-rep"].id,
            )
        )
    await db_session.commit()
    return {"pipeline": pipeline, "stages": stages}


@pytest_asyncio.fixture
async def seed_100_contacts(db_session, seeded_org):
    from backend.models import Contact

    for index in range(100):
        db_session.add(
            Contact(
                org_id=seeded_org["org"].id,
                first_name=f"First{index}",
                last_name=f"Last{index}",
                email=f"user{index}@example.com",
                lifecycle_stage="lead" if index % 2 == 0 else "customer",
                owner_id=seeded_org["alpha-rep"].id,
            )
        )
    await db_session.commit()
    return seeded_org["org"]


@pytest_asyncio.fixture
async def seed_50_pages(db_session, seeded_org):
    from backend.models import Page

    pages = []
    for index in range(50):
        page = Page(
            org_id=seeded_org["org"].id,
            team_id=seeded_org["alpha"].id,
            title=f"Page {index}",
            content={"type": "doc", "content": []},
            parent_page_id=pages[-1].id if pages and index % 5 else None,
            created_by=seeded_org["alpha-rep"].id,
            last_edited_by=seeded_org["alpha-rep"].id,
        )
        db_session.add(page)
        await db_session.flush()
        pages.append(page)
    await db_session.commit()
    return pages


@pytest_asyncio.fixture
async def seed_1000_activities(db_session, seeded_org, pipeline, stages):
    deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Activity Heavy Deal",
        value=1000,
        probability=15,
        status="open",
        owner_id=seeded_org["alpha-rep"].id,
    )
    db_session.add(deal)
    await db_session.flush()
    for index in range(1000):
        db_session.add(
            DealActivity(
                deal_id=deal.id,
                user_id=seeded_org["alpha-rep"].id,
                activity_type="email",
                title=f"Activity {index}",
                occurred_at=datetime.now(timezone.utc) - timedelta(minutes=index),
            )
        )
    await db_session.commit()
    return deal


@pytest_asyncio.fixture
async def seed_ref_data(db_session, seeded_org):
    """Insert one row per category for tests that don't run the full migration."""
    from backend.models import RefData

    categories = [
        ("sector", "financial_services", "Financial Services"),
        ("sub_sector", "software_saas", "Software & SaaS"),
        ("transaction_type", "equity", "Equity"),
        ("tier", "tier_1", "Tier 1"),
        ("contact_type", "lp", "LP"),
        ("company_type", "financial_sponsor", "Financial Sponsor"),
        ("company_sub_type", "buyout", "Buyout"),
        ("deal_source_type", "proprietary", "Proprietary"),
        ("passed_dead_reason", "valuation", "Valuation"),
        ("investor_type", "swf", "SWF"),
        ("fund_status", "fundraising", "Fundraising"),
        ("fund_status", "closed", "Closed"),
        ("fund_status", "deployed", "Deployed"),
        ("fund_status", "returning_capital", "Returning Capital"),
    ]
    rows = [
        RefData(org_id=None, category=cat, value=val, label=lbl, position=0, is_active=True)
        for cat, val, lbl in categories
    ]
    db_session.add_all(rows)
    await db_session.commit()
    return rows


@pytest_asyncio.fixture
async def query_counter():
    engine = get_engine()
    counts = {"count": 0}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if not statement.lstrip().upper().startswith(("BEGIN", "COMMIT", "ROLLBACK", "PRAGMA")):
            counts["count"] += 1

    event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield counts
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
