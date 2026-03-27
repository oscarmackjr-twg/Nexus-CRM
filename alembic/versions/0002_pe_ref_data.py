"""pe_ref_data — create ref_data table and seed all 10 TWG categories"""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime, timezone

revision = "0002_pe_ref_data"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

# Ad-hoc table reference for bulk_insert (Alembic requirement)
ref_data_table = sa.table(
    "ref_data",
    sa.column("id", sa.String),
    sa.column("org_id", sa.String),
    sa.column("category", sa.String),
    sa.column("value", sa.String),
    sa.column("label", sa.String),
    sa.column("position", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)


def _row(category: str, value: str, label: str, position: int = 0) -> dict:
    return {
        "id": str(uuid4()),
        "org_id": None,
        "category": category,
        "value": value,
        "label": label,
        "position": position,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }


def upgrade() -> None:
    op.create_table(
        "ref_data",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "org_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "org_id", "category", "value", name="uq_ref_data_org_category_value"
        ),
    )
    op.create_index(
        "ix_ref_data_org_category", "ref_data", ["org_id", "category"]
    )

    rows = [
        # ------------------------------------------------------------------
        # sector (REFDATA-03) — 10 rows
        # ------------------------------------------------------------------
        _row("sector", "financial_services", "Financial Services", 0),
        _row("sector", "technology", "Technology", 1),
        _row("sector", "healthcare", "Healthcare", 2),
        _row("sector", "real_estate", "Real Estate", 3),
        _row("sector", "infrastructure", "Infrastructure", 4),
        _row("sector", "consumer", "Consumer", 5),
        _row("sector", "industrials", "Industrials", 6),
        _row("sector", "energy", "Energy", 7),
        _row("sector", "media_telecom", "Media & Telecom", 8),
        _row("sector", "business_services", "Business Services", 9),
        # ------------------------------------------------------------------
        # sub_sector (REFDATA-02 + D-01) — PE-relevant, ~3-5 per sector
        # ------------------------------------------------------------------
        # Technology
        _row("sub_sector", "software_saas", "Software & SaaS", 0),
        _row("sub_sector", "fintech", "Fintech", 1),
        _row("sub_sector", "healthtech", "Healthtech", 2),
        _row("sub_sector", "hardware_semiconductors", "Hardware & Semiconductors", 3),
        # Healthcare
        _row("sub_sector", "healthcare_it", "Healthcare IT", 4),
        _row("sub_sector", "pharma_biotech", "Pharma & Biotech", 5),
        _row("sub_sector", "medical_devices", "Medical Devices", 6),
        # Financial Services
        _row("sub_sector", "asset_management", "Asset Management", 7),
        _row("sub_sector", "banking", "Banking", 8),
        _row("sub_sector", "insurance", "Insurance", 9),
        # Real Estate
        _row("sub_sector", "residential", "Residential", 10),
        _row("sub_sector", "commercial", "Commercial", 11),
        _row("sub_sector", "industrial_re", "Industrial", 12),
        # Infrastructure
        _row("sub_sector", "energy_renewables", "Energy & Renewables", 13),
        _row("sub_sector", "transportation", "Transportation", 14),
        _row("sub_sector", "utilities", "Utilities", 15),
        # Consumer
        _row("sub_sector", "retail", "Retail", 16),
        _row("sub_sector", "food_beverage", "Food & Beverage", 17),
        _row("sub_sector", "luxury", "Luxury", 18),
        # Industrials
        _row("sub_sector", "manufacturing", "Manufacturing", 19),
        _row("sub_sector", "logistics", "Logistics", 20),
        _row("sub_sector", "chemicals", "Chemicals", 21),
        # Energy
        _row("sub_sector", "oil_gas", "Oil & Gas", 22),
        _row("sub_sector", "renewables", "Renewables", 23),
        _row("sub_sector", "power_generation", "Power Generation", 24),
        # Media & Telecom
        _row("sub_sector", "media", "Media", 25),
        _row("sub_sector", "telecom", "Telecom", 26),
        # Business Services
        _row("sub_sector", "consulting", "Consulting", 27),
        _row("sub_sector", "outsourcing", "Outsourcing", 28),
        _row("sub_sector", "hr_staffing", "HR & Staffing", 29),
        # ------------------------------------------------------------------
        # transaction_type (REFDATA-04)
        # ------------------------------------------------------------------
        _row("transaction_type", "equity", "Equity", 0),
        _row("transaction_type", "credit", "Credit", 1),
        _row("transaction_type", "preferred_equity", "Preferred Equity", 2),
        _row("transaction_type", "mezzanine", "Mezzanine", 3),
        _row("transaction_type", "growth_equity", "Growth Equity", 4),
        _row("transaction_type", "buyout", "Buyout", 5),
        _row("transaction_type", "debt_advisory", "Debt Advisory", 6),
        _row("transaction_type", "ma_advisory", "M&A Advisory", 7),
        # ------------------------------------------------------------------
        # tier (REFDATA-05)
        # ------------------------------------------------------------------
        _row("tier", "tier_1", "Tier 1", 0),
        _row("tier", "tier_2", "Tier 2", 1),
        _row("tier", "tier_3", "Tier 3", 2),
        # ------------------------------------------------------------------
        # contact_type (REFDATA-06)
        # ------------------------------------------------------------------
        _row("contact_type", "lp", "LP", 0),
        _row("contact_type", "gp", "GP", 1),
        _row("contact_type", "advisor", "Advisor", 2),
        _row("contact_type", "management", "Management", 3),
        _row("contact_type", "lender", "Lender", 4),
        _row("contact_type", "co_investor", "Co-Investor", 5),
        _row("contact_type", "strategic", "Strategic", 6),
        # ------------------------------------------------------------------
        # company_type (REFDATA-07)
        # ------------------------------------------------------------------
        _row("company_type", "financial_sponsor", "Financial Sponsor", 0),
        _row("company_type", "strategic_company", "Strategic", 1),
        _row("company_type", "family_office", "Family Office", 2),
        _row("company_type", "sovereign_wealth_fund", "Sovereign Wealth Fund", 3),
        _row("company_type", "pension_fund", "Pension Fund", 4),
        _row("company_type", "insurance_company", "Insurance Company", 5),
        _row("company_type", "bank", "Bank", 6),
        _row("company_type", "operating_company", "Operating Company", 7),
        # ------------------------------------------------------------------
        # company_sub_type (REFDATA-02 — Claude selects PE-relevant values)
        # ------------------------------------------------------------------
        _row("company_sub_type", "buyout", "Buyout", 0),
        _row("company_sub_type", "growth", "Growth", 1),
        _row("company_sub_type", "venture", "Venture", 2),
        _row("company_sub_type", "credit_fund", "Credit", 3),
        _row("company_sub_type", "real_assets", "Real Assets", 4),
        _row("company_sub_type", "hedge_fund", "Hedge Fund", 5),
        _row("company_sub_type", "infrastructure_fund", "Infrastructure Fund", 6),
        # ------------------------------------------------------------------
        # deal_source_type (REFDATA-08)
        # ------------------------------------------------------------------
        _row("deal_source_type", "proprietary", "Proprietary", 0),
        _row("deal_source_type", "bank_source", "Bank", 1),
        _row("deal_source_type", "advisor_source", "Advisor", 2),
        _row("deal_source_type", "management_source", "Management", 3),
        _row("deal_source_type", "portfolio_company", "Portfolio Company", 4),
        _row("deal_source_type", "existing_lp", "Existing LP", 5),
        # ------------------------------------------------------------------
        # passed_dead_reason (REFDATA-09)
        # ------------------------------------------------------------------
        _row("passed_dead_reason", "valuation", "Valuation", 0),
        _row("passed_dead_reason", "diligence", "Diligence", 1),
        _row("passed_dead_reason", "market_conditions", "Market Conditions", 2),
        _row("passed_dead_reason", "competitive", "Competitive", 3),
        _row("passed_dead_reason", "strategic_fit", "Strategic Fit", 4),
        _row("passed_dead_reason", "timing", "Timing", 5),
        _row("passed_dead_reason", "management_reason", "Management", 6),
        _row("passed_dead_reason", "no_follow_up", "No Follow-Up", 7),
        # ------------------------------------------------------------------
        # investor_type (REFDATA-10)
        # ------------------------------------------------------------------
        _row("investor_type", "swf", "SWF", 0),
        _row("investor_type", "pension_super", "Pension/Super", 1),
        _row("investor_type", "corporate", "Corporate", 2),
        _row("investor_type", "family_office_inv", "Family Office", 3),
        _row("investor_type", "financial_sponsor_inv", "Financial Sponsor", 4),
        _row("investor_type", "insurance_inv", "Insurance", 5),
        _row("investor_type", "bank_inv", "Bank", 6),
    ]

    op.bulk_insert(ref_data_table, rows)


def downgrade() -> None:
    op.drop_index("ix_ref_data_org_category", table_name="ref_data")
    op.drop_table("ref_data")
