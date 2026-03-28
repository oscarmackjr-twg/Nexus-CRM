"""deal_funding — create deal_funding table and seed deal_funding_status ref_data

Revision ID: 0011_deal_funding
Revises: 0010_deal_counterparties
Create Date: 2026-03-28

"""

from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_deal_funding"
down_revision: Union[str, Sequence[str]] = "0010_deal_counterparties"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Ad-hoc table reference for bulk_insert (Alembic requirement)
ref_data_table = sa.table(
    "ref_data",
    sa.column("id", sa.Uuid),
    sa.column("org_id", sa.Uuid),
    sa.column("category", sa.String),
    sa.column("value", sa.String),
    sa.column("label", sa.String),
    sa.column("position", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime),
)


def upgrade() -> None:
    op.create_table(
        "deal_funding",
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
            "capital_provider_id",
            sa.Uuid(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status_id",
            sa.Uuid(),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("projected_commitment_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("projected_commitment_currency", sa.String(3), nullable=True),
        sa.Column("actual_commitment_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("actual_commitment_currency", sa.String(3), nullable=True),
        sa.Column("actual_commitment_date", sa.Date(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column("comments_next_steps", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_deal_funding_deal_id", "deal_funding", ["deal_id"])
    op.create_index("ix_deal_funding_capital_provider_id", "deal_funding", ["capital_provider_id"])

    # Seed deal_funding_status ref_data (system defaults, org_id=None)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        ref_data_table,
        [
            {
                "id": uuid4(),
                "org_id": None,
                "category": "deal_funding_status",
                "value": "soft_circle",
                "label": "Soft Circle",
                "position": 1,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": uuid4(),
                "org_id": None,
                "category": "deal_funding_status",
                "value": "hard_circle",
                "label": "Hard Circle",
                "position": 2,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": uuid4(),
                "org_id": None,
                "category": "deal_funding_status",
                "value": "committed",
                "label": "Committed",
                "position": 3,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": uuid4(),
                "org_id": None,
                "category": "deal_funding_status",
                "value": "funded",
                "label": "Funded",
                "position": 4,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": uuid4(),
                "org_id": None,
                "category": "deal_funding_status",
                "value": "declined",
                "label": "Declined",
                "position": 5,
                "is_active": True,
                "created_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM ref_data WHERE category = 'deal_funding_status'")
    op.drop_index("ix_deal_funding_capital_provider_id", table_name="deal_funding")
    op.drop_index("ix_deal_funding_deal_id", table_name="deal_funding")
    op.drop_table("deal_funding")
