import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.auth.security import hash_password
from backend.database import Base, get_engine, get_session_maker
from backend.models import Company, Contact, Deal, DealActivity, Fund, Organization, Pipeline, PipelineStage, Team, User


async def seed() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_maker()
    async with session_factory() as session:
        org = await session.scalar(select(Organization).where(Organization.slug == "demo-org"))
        if org is None:
            org = Organization(name="Demo Organization", slug="demo-org", plan="growth")
            session.add(org)
            await session.flush()

        team = await session.scalar(select(Team).where(Team.org_id == org.id, Team.name == "Revenue Team"))
        if team is None:
            team = Team(org_id=org.id, name="Revenue Team", type="sales")
            session.add(team)
            await session.flush()

        admin = await session.scalar(select(User).where(User.email == "admin@demo.local"))
        if admin is None:
            admin = User(
                org_id=org.id,
                team_id=team.id,
                email="admin@demo.local",
                username="demo-admin",
                hashed_password=hash_password("password123"),
                full_name="Demo Admin",
                role="org_admin",
            )
            session.add(admin)
            await session.flush()

        pipeline = await session.scalar(select(Pipeline).where(Pipeline.org_id == org.id, Pipeline.name == "New Business"))
        if pipeline is None:
            pipeline = Pipeline(org_id=org.id, team_id=team.id, name="New Business", is_default=True, created_by=admin.id)
            session.add(pipeline)
            await session.flush()

        stage_specs = [
            ("Qualified", 1, 20, "open"),
            ("Proposal", 2, 50, "open"),
            ("Closed Won", 3, 100, "won"),
            ("Closed Lost", 4, 0, "lost"),
        ]
        for name, position, probability, stage_type in stage_specs:
            existing = await session.scalar(
                select(PipelineStage).where(PipelineStage.pipeline_id == pipeline.id, PipelineStage.position == position)
            )
            if existing is None:
                session.add(
                    PipelineStage(
                        pipeline_id=pipeline.id,
                        name=name,
                        position=position,
                        probability=probability,
                        stage_type=stage_type,
                    )
                )

        await session.commit()

        # Load stage IDs
        stages = (await session.scalars(
            select(PipelineStage).where(PipelineStage.pipeline_id == pipeline.id)
        )).all()
        stage_map = {s.name: s for s in stages}
        stage_qualified  = stage_map.get("Qualified")
        stage_proposal   = stage_map.get("Proposal")
        stage_won        = stage_map.get("Closed Won")
        stage_lost       = stage_map.get("Closed Lost")

        # ── Fund ─────────────────────────────────────────────────────────────
        fund = await session.scalar(select(Fund).where(Fund.org_id == org.id, Fund.fund_name == "Nexus Capital Fund III"))
        if fund is None:
            fund = Fund(
                org_id=org.id,
                fund_name="Nexus Capital Fund III",
                target_fund_size_amount=Decimal("500000000"),
                target_fund_size_currency="USD",
                vintage_year=2021,
            )
            session.add(fund)
            await session.flush()

        # ── Companies ────────────────────────────────────────────────────────
        company_specs = [
            dict(name="Apex Distribution LLC",        domain="apexdist.com",    industry="Distribution",           size_range="201-500",  annual_revenue=Decimal("87000000")),
            dict(name="Meridian Healthcare Partners", domain="meridianhealth.com", industry="Healthcare Services",  size_range="501-1000", annual_revenue=Decimal("142000000")),
            dict(name="Clearwater Technologies",      domain="clearwatertech.io", industry="Software",              size_range="51-200",   annual_revenue=Decimal("31000000")),
            dict(name="Summit Industrial Holdings",   domain="summitind.com",   industry="Manufacturing",           size_range="201-500",  annual_revenue=Decimal("63000000")),
        ]
        companies = {}
        for spec in company_specs:
            co = await session.scalar(select(Company).where(Company.org_id == org.id, Company.name == spec["name"]))
            if co is None:
                co = Company(org_id=org.id, owner_id=admin.id, **spec)
                session.add(co)
            companies[spec["name"]] = co
        await session.flush()

        # ── Contacts ─────────────────────────────────────────────────────────
        contact_specs = [
            dict(first_name="James",   last_name="Whitmore", email="james.whitmore@apexdist.com",     title="CEO",                 company_name="Apex Distribution LLC",        lifecycle_stage="customer"),
            dict(first_name="Sarah",   last_name="Chen",     email="sarah.chen@apexdist.com",          title="CFO",                 company_name="Apex Distribution LLC",        lifecycle_stage="customer"),
            dict(first_name="Robert",  last_name="Davis",    email="robert.davis@meridianhealth.com",  title="CEO",                 company_name="Meridian Healthcare Partners",  lifecycle_stage="qualified"),
            dict(first_name="Michael", last_name="Torres",   email="michael.torres@morganstanley.com", title="Managing Director",   company_name=None,                           lifecycle_stage="qualified"),
            dict(first_name="Lisa",    last_name="Park",     email="lisa.park@baml.com",               title="VP Investment Banking", company_name=None,                         lifecycle_stage="lead"),
            dict(first_name="David",   last_name="Huang",    email="david.huang@clearwatertech.io",    title="Founder & CEO",       company_name="Clearwater Technologies",      lifecycle_stage="qualified"),
        ]
        contacts = {}
        for spec in contact_specs:
            company_name = spec.pop("company_name")
            existing = await session.scalar(select(Contact).where(Contact.org_id == org.id, Contact.email == spec["email"]))
            if existing is None:
                existing = Contact(
                    org_id=org.id,
                    owner_id=admin.id,
                    company_id=companies[company_name].id if company_name else None,
                    **spec,
                )
                session.add(existing)
            contacts[spec["email"]] = existing
        await session.flush()

        # ── Deals ─────────────────────────────────────────────────────────────
        deal_specs = [
            dict(
                name="Apex Distribution — Platform Buyout",
                stage=stage_proposal,   status="open",  value=Decimal("28500000"), probability=Decimal("50"),
                expected_close_date=date(2026, 6, 30),
                company_name="Apex Distribution LLC",
                contact_email="james.whitmore@apexdist.com",
                description="Mid-market buyout of a regional distribution platform. CIM received; team preparing IOI.",
                revenue_amount=Decimal("87000000"), revenue_currency="USD",
                ebitda_amount=Decimal("9100000"),   ebitda_currency="USD",
                new_deal_date=date(2026, 1, 15),
                cim_received_date=date(2026, 2, 3),
                ioi_due_date=date(2026, 4, 10),
            ),
            dict(
                name="Meridian Healthcare — Add-on Acquisition",
                stage=stage_qualified,  status="open",  value=Decimal("14200000"), probability=Decimal("20"),
                expected_close_date=date(2026, 9, 15),
                company_name="Meridian Healthcare Partners",
                contact_email="robert.davis@meridianhealth.com",
                description="Healthcare services add-on to complement existing portfolio. In initial screening.",
                revenue_amount=Decimal("142000000"), revenue_currency="USD",
                ebitda_amount=Decimal("18600000"),   ebitda_currency="USD",
                new_deal_date=date(2026, 3, 1),
            ),
            dict(
                name="Clearwater Technologies — Growth Equity",
                stage=stage_proposal,   status="open",  value=Decimal("9500000"), probability=Decimal("50"),
                expected_close_date=date(2026, 7, 31),
                company_name="Clearwater Technologies",
                contact_email="david.huang@clearwatertech.io",
                description="Series B growth equity round. SaaS platform with 85% gross margins and strong NRR.",
                revenue_amount=Decimal("31000000"), revenue_currency="USD",
                ebitda_amount=Decimal("4200000"),   ebitda_currency="USD",
                new_deal_date=date(2026, 2, 20),
                cim_received_date=date(2026, 3, 5),
                ioi_due_date=date(2026, 4, 25),
                ioi_submitted_date=date(2026, 4, 24),
            ),
            dict(
                name="Summit Industrial — Platform Build",
                stage=stage_qualified,  status="open",  value=Decimal("22000000"), probability=Decimal("20"),
                expected_close_date=date(2026, 10, 31),
                company_name="Summit Industrial Holdings",
                contact_email=None,
                description="Industrial manufacturing platform play in fragmented niche. Early diligence phase.",
                revenue_amount=Decimal("63000000"), revenue_currency="USD",
                ebitda_amount=Decimal("7800000"),   ebitda_currency="USD",
                new_deal_date=date(2026, 3, 10),
            ),
            dict(
                name="Riverstone Logistics — Buyout",
                stage=stage_won,        status="won",   value=Decimal("31000000"), probability=Decimal("100"),
                expected_close_date=date(2025, 12, 15),
                actual_close_date=date(2025, 12, 18),
                company_name=None, contact_email=None,
                description="Completed buyout of logistics company. Now a portfolio company.",
                revenue_amount=Decimal("95000000"), revenue_currency="USD",
                ebitda_amount=Decimal("12500000"),  ebitda_currency="USD",
                enterprise_value_amount=Decimal("106250000"), enterprise_value_currency="USD",
                equity_investment_amount=Decimal("31000000"), equity_investment_currency="USD",
                portfolio_company_date=date(2025, 12, 18),
            ),
            dict(
                name="TechBridge Solutions — Passed",
                stage=stage_lost,       status="lost",  value=Decimal("0"), probability=Decimal("0"),
                expected_close_date=date(2026, 2, 28),
                company_name=None, contact_email=None,
                description="SaaS platform — passed on valuation grounds after management presentation.",
                passed_dead_date=date(2026, 2, 15),
                passed_dead_commentary="Seller expectations well above our maximum bid at 18x EBITDA. Could not bridge the gap.",
            ),
        ]

        for spec in deal_specs:
            existing = await session.scalar(select(Deal).where(Deal.org_id == org.id, Deal.name == spec["name"]))
            if existing is None:
                stage = spec.pop("stage")
                company_name = spec.pop("company_name")
                contact_email = spec.pop("contact_email")
                deal = Deal(
                    org_id=org.id,
                    team_id=team.id,
                    pipeline_id=pipeline.id,
                    stage_id=stage.id,
                    owner_id=admin.id,
                    fund_id=fund.id,
                    currency="USD",
                    company_id=companies[company_name].id if company_name else None,
                    contact_id=contacts[contact_email].id if contact_email else None,
                    **spec,
                )
                session.add(deal)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
