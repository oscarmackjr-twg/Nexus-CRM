"""fund — create funds table and seed fund_status ref_data

Revision ID: 0007_fund
Revises: 0006_activity_deal_id_nullable
Create Date: 2026-03-27

"""

from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_fund"
down_revision: Union[str, Sequence[str]] = "0006_activity_deal_id_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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


def upgrade() -> None:
    op.create_table(
        "funds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "org_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fund_name", sa.String(255), nullable=False),
        sa.Column(
            "fundraise_status_id",
            sa.String(36),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_fund_size_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("target_fund_size_currency", sa.String(3), nullable=True),
        sa.Column("vintage_year", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_funds_org_id", "funds", ["org_id"])

    # Seed fund_status ref_data (system defaults, org_id=None)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        ref_data_table,
        [
            {
                "id": str(uuid4()),
                "org_id": None,
                "category": "fund_status",
                "value": "fundraising",
                "label": "Fundraising",
                "position": 1,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": str(uuid4()),
                "org_id": None,
                "category": "fund_status",
                "value": "closed",
                "label": "Closed",
                "position": 2,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": str(uuid4()),
                "org_id": None,
                "category": "fund_status",
                "value": "deployed",
                "label": "Deployed",
                "position": 3,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": str(uuid4()),
                "org_id": None,
                "category": "fund_status",
                "value": "returning_capital",
                "label": "Returning Capital",
                "position": 4,
                "is_active": True,
                "created_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM ref_data WHERE category = 'fund_status'")
    op.drop_index("ix_funds_org_id", table_name="funds")
    op.drop_table("funds")
