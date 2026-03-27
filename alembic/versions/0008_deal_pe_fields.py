"""deal_pe_fields — add PE Blueprint columns to deals table

Revision ID: 0008_deal_pe_fields
Revises: 0007_fund
Create Date: 2026-03-27

"""

from alembic import op
import sqlalchemy as sa

revision = "0008_deal_pe_fields"
down_revision = "0007_fund"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # DEAL-01: Identity fields
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("deals", sa.Column("new_deal_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("transaction_type_id", sa.String(36), nullable=True))
    op.add_column("deals", sa.Column("fund_id", sa.String(36), nullable=True))
    op.add_column("deals", sa.Column("platform_or_addon", sa.String(20), nullable=True))
    op.add_column("deals", sa.Column("platform_company_id", sa.String(36), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-04: Source tracking fields
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("source_type_id", sa.String(36), nullable=True))
    op.add_column("deals", sa.Column("source_company_id", sa.String(36), nullable=True))
    op.add_column("deals", sa.Column("source_individual_id", sa.String(36), nullable=True))
    op.add_column("deals", sa.Column("originator_id", sa.String(36), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-05: Financial fields (amount + currency pairs)
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("revenue_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("revenue_currency", sa.String(3), nullable=True))
    op.add_column("deals", sa.Column("ebitda_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("ebitda_currency", sa.String(3), nullable=True))
    op.add_column("deals", sa.Column("enterprise_value_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("enterprise_value_currency", sa.String(3), nullable=True))
    op.add_column("deals", sa.Column("equity_investment_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("equity_investment_currency", sa.String(3), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-06: Bid fields
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("loi_bid_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("loi_bid_currency", sa.String(3), nullable=True))
    op.add_column("deals", sa.Column("ioi_bid_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("deals", sa.Column("ioi_bid_currency", sa.String(3), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-07: Date milestone fields
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("cim_received_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("ioi_due_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("ioi_submitted_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("management_presentation_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("loi_due_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("loi_submitted_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("live_diligence_date", sa.Date(), nullable=True))
    op.add_column("deals", sa.Column("portfolio_company_date", sa.Date(), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-08: Passed/dead fields
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("passed_dead_date", sa.Date(), nullable=True))
    # Use sa.JSON not sa.JSONB for SQLite compatibility (research pitfall 7)
    op.add_column("deals", sa.Column("passed_dead_reasons", sa.JSON(), nullable=True))
    op.add_column("deals", sa.Column("passed_dead_commentary", sa.Text(), nullable=True))

    # ------------------------------------------------------------------
    # DEAL-09: Legacy ID + org-scoped unique constraint
    # ------------------------------------------------------------------
    op.add_column("deals", sa.Column("legacy_id", sa.String(100), nullable=True))
    op.create_unique_constraint("uq_deals_org_legacy_id", "deals", ["org_id", "legacy_id"])

    # ------------------------------------------------------------------
    # Named FK constraints (separate from add_column for clean naming)
    # ------------------------------------------------------------------
    op.create_foreign_key(
        "fk_deals_transaction_type_id", "deals", "ref_data", ["transaction_type_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_fund_id", "deals", "funds", ["fund_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_platform_company_id", "deals", "companies", ["platform_company_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_source_type_id", "deals", "ref_data", ["source_type_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_source_company_id", "deals", "companies", ["source_company_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_source_individual_id", "deals", "contacts", ["source_individual_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_deals_originator_id", "deals", "users", ["originator_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    # Drop unique constraint first
    op.drop_constraint("uq_deals_org_legacy_id", "deals", type_="unique")

    # Drop named FK constraints
    op.drop_constraint("fk_deals_originator_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_source_individual_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_source_company_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_source_type_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_platform_company_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_fund_id", "deals", type_="foreignkey")
    op.drop_constraint("fk_deals_transaction_type_id", "deals", type_="foreignkey")

    # Drop columns in reverse order
    op.drop_column("deals", "legacy_id")
    op.drop_column("deals", "passed_dead_commentary")
    op.drop_column("deals", "passed_dead_reasons")
    op.drop_column("deals", "passed_dead_date")
    op.drop_column("deals", "portfolio_company_date")
    op.drop_column("deals", "live_diligence_date")
    op.drop_column("deals", "loi_submitted_date")
    op.drop_column("deals", "loi_due_date")
    op.drop_column("deals", "management_presentation_date")
    op.drop_column("deals", "ioi_submitted_date")
    op.drop_column("deals", "ioi_due_date")
    op.drop_column("deals", "cim_received_date")
    op.drop_column("deals", "ioi_bid_currency")
    op.drop_column("deals", "ioi_bid_amount")
    op.drop_column("deals", "loi_bid_currency")
    op.drop_column("deals", "loi_bid_amount")
    op.drop_column("deals", "equity_investment_currency")
    op.drop_column("deals", "equity_investment_amount")
    op.drop_column("deals", "enterprise_value_currency")
    op.drop_column("deals", "enterprise_value_amount")
    op.drop_column("deals", "ebitda_currency")
    op.drop_column("deals", "ebitda_amount")
    op.drop_column("deals", "revenue_currency")
    op.drop_column("deals", "revenue_amount")
    op.drop_column("deals", "originator_id")
    op.drop_column("deals", "source_individual_id")
    op.drop_column("deals", "source_company_id")
    op.drop_column("deals", "source_type_id")
    op.drop_column("deals", "platform_company_id")
    op.drop_column("deals", "platform_or_addon")
    op.drop_column("deals", "fund_id")
    op.drop_column("deals", "transaction_type_id")
    op.drop_column("deals", "new_deal_date")
    op.drop_column("deals", "description")
