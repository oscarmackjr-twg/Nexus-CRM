"""deal_counterparties — create deal_counterparties table for per-deal investor pipeline tracking

Revision ID: 0010_deal_counterparties
Revises: 0009_deal_team_members
Create Date: 2026-03-28

"""

from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_deal_counterparties"
down_revision: Union[str, Sequence[str]] = "0009_deal_team_members"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_counterparties",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "deal_id",
            sa.Uuid(),
            sa.ForeignKey("deals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("primary_contact_name", sa.String(255), nullable=True),
        sa.Column("primary_contact_email", sa.String(255), nullable=True),
        sa.Column("primary_contact_phone", sa.String(50), nullable=True),
        # Stage tracking dates (CPARTY-02)
        sa.Column("nda_sent_at", sa.Date(), nullable=True),
        sa.Column("nda_signed_at", sa.Date(), nullable=True),
        sa.Column("nrl_signed_at", sa.Date(), nullable=True),
        sa.Column("intro_materials_sent_at", sa.Date(), nullable=True),
        sa.Column("vdr_access_granted_at", sa.Date(), nullable=True),
        sa.Column("feedback_received_at", sa.Date(), nullable=True),
        # Ref_data FKs (CPARTY-03)
        sa.Column(
            "tier_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "investor_type_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Financial fields (CPARTY-04)
        sa.Column("check_size_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("check_size_currency", sa.String(3), nullable=True),
        sa.Column("aum_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("aum_currency", sa.String(3), nullable=True),
        sa.Column("next_steps", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("deal_id", "company_id", name="uq_deal_counterparties_deal_company"),
    )
    op.create_index("ix_deal_counterparties_deal_id", "deal_counterparties", ["deal_id"])
    op.create_index("ix_deal_counterparties_company_id", "deal_counterparties", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_counterparties_company_id", table_name="deal_counterparties")
    op.drop_index("ix_deal_counterparties_deal_id", table_name="deal_counterparties")
    op.drop_table("deal_counterparties")
