"""deal_team_members — create M2M association table for deal team membership

Revision ID: 0009_deal_team_members
Revises: 0008_deal_pe_fields
Create Date: 2026-03-27

"""

from alembic import op
import sqlalchemy as sa

revision = "0009_deal_team_members"
down_revision = "0008_deal_pe_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_team_members",
        sa.Column("deal_id", sa.String(36), sa.ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_deal_team_members_deal_id", "deal_team_members", ["deal_id"])
    op.create_index("ix_deal_team_members_user_id", "deal_team_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_team_members_user_id", table_name="deal_team_members")
    op.drop_index("ix_deal_team_members_deal_id", table_name="deal_team_members")
    op.drop_table("deal_team_members")
