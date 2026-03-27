"""activity deal_id nullable + contact_id FK

Revision ID: 0006_activity_deal_id_nullable
Revises: 0004_contact_coverage_persons, 0005_company_pe_fields
Create Date: 2026-03-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_activity_deal_id_nullable"
down_revision: Union[str, Sequence[str]] = ("0004_contact_coverage_persons", "0005_company_pe_fields")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make deal_id nullable on deal_activities (currently NOT NULL)
    with op.batch_alter_table("deal_activities") as batch_op:
        batch_op.alter_column("deal_id", nullable=True)

    # Add contact_id FK column
    op.add_column(
        "deal_activities",
        sa.Column(
            "contact_id",
            sa.String(36),
            sa.ForeignKey("contacts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_deal_activities_contact_id", "deal_activities", ["contact_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_activities_contact_id", "deal_activities")
    op.drop_column("deal_activities", "contact_id")
    with op.batch_alter_table("deal_activities") as batch_op:
        batch_op.alter_column("deal_id", nullable=False)
