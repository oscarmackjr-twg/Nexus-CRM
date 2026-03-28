"""company_pe_fields — add all PE Blueprint columns to companies table"""
from alembic import op
import sqlalchemy as sa

revision = "0005_company_pe_fields"
down_revision = "0002_pe_ref_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # COMPANY-01: Identity fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column(
            "company_type_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column("company_sub_type_ids", sa.JSON(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("description", sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------
    # COMPANY-02: Phone + parent
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("main_phone", sa.String(50), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column(
            "parent_company_id",
            sa.Uuid(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------------
    # COMPANY-03: Address fields (country does NOT exist yet)
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("address", sa.Text(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("city", sa.String(100), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("state", sa.String(100), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("postal_code", sa.String(20), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("country", sa.String(100), nullable=True),
    )

    # ------------------------------------------------------------------
    # COMPANY-04: Ref_data FK fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column(
            "tier_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "sector_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "sub_sector_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------------
    # COMPANY-05: Investment preference fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("sector_preferences", sa.JSON(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("sub_sector_preferences", sa.JSON(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("preference_notes", sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------
    # COMPANY-06: Financial fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("aum_amount", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("aum_currency", sa.String(3), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("ebitda_amount", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("ebitda_currency", sa.String(3), nullable=True),
    )

    # ------------------------------------------------------------------
    # COMPANY-07: Bite size + co-invest
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("typical_bite_size_low", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("typical_bite_size_high", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("bite_size_currency", sa.String(3), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("co_invest", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column(
            "target_deal_size_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------------
    # COMPANY-08: Deal preference fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("transaction_types", sa.JSON(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("min_ebitda", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("max_ebitda", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("ebitda_range_currency", sa.String(3), nullable=True),
    )

    # ------------------------------------------------------------------
    # COMPANY-09: Relationship fields
    # ------------------------------------------------------------------
    op.add_column(
        "companies",
        sa.Column("watchlist", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column(
            "coverage_person_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column("contact_frequency", sa.Integer(), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("legacy_id", sa.String(100), nullable=True),
    )

    # Org-scoped unique constraint on legacy_id
    op.create_unique_constraint(
        "uq_companies_org_legacy_id", "companies", ["org_id", "legacy_id"]
    )


def downgrade() -> None:
    # Drop constraint first
    op.drop_constraint("uq_companies_org_legacy_id", "companies", type_="unique")

    # Drop columns in reverse order
    op.drop_column("companies", "legacy_id")
    op.drop_column("companies", "contact_frequency")
    op.drop_column("companies", "coverage_person_id")
    op.drop_column("companies", "watchlist")
    op.drop_column("companies", "ebitda_range_currency")
    op.drop_column("companies", "max_ebitda")
    op.drop_column("companies", "min_ebitda")
    op.drop_column("companies", "transaction_types")
    op.drop_column("companies", "target_deal_size_id")
    op.drop_column("companies", "co_invest")
    op.drop_column("companies", "bite_size_currency")
    op.drop_column("companies", "typical_bite_size_high")
    op.drop_column("companies", "typical_bite_size_low")
    op.drop_column("companies", "ebitda_currency")
    op.drop_column("companies", "ebitda_amount")
    op.drop_column("companies", "aum_currency")
    op.drop_column("companies", "aum_amount")
    op.drop_column("companies", "preference_notes")
    op.drop_column("companies", "sub_sector_preferences")
    op.drop_column("companies", "sector_preferences")
    op.drop_column("companies", "sub_sector_id")
    op.drop_column("companies", "sector_id")
    op.drop_column("companies", "tier_id")
    op.drop_column("companies", "country")
    op.drop_column("companies", "postal_code")
    op.drop_column("companies", "state")
    op.drop_column("companies", "city")
    op.drop_column("companies", "address")
    op.drop_column("companies", "parent_company_id")
    op.drop_column("companies", "main_phone")
    op.drop_column("companies", "description")
    op.drop_column("companies", "company_sub_type_ids")
    op.drop_column("companies", "company_type_id")
