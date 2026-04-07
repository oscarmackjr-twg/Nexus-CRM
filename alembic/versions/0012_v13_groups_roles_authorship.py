"""v1.3 groups roles authorship — add Team.is_active, authorship columns, rename role values

Revision ID: 0012_v13_groups_roles_authorship
Revises: 0011_deal_funding
Create Date: 2026-04-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_v13_groups_roles_authorship"
down_revision: Union[str, Sequence[str]] = "0011_deal_funding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_active to teams
    op.add_column(
        "teams",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
    )

    # 2. Add authorship columns to contacts
    op.add_column(
        "contacts",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "contacts",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 3. Add authorship columns to companies
    op.add_column(
        "companies",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "companies",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 4. Add authorship columns to deals
    op.add_column(
        "deals",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "deals",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 5. Add authorship columns + updated_at to funds (funds lacks updated_at)
    op.add_column(
        "funds",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.add_column(
        "funds",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "funds",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 6. Add authorship columns to deal_counterparties
    op.add_column(
        "deal_counterparties",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "deal_counterparties",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 7. Add authorship columns to deal_funding
    op.add_column(
        "deal_funding",
        sa.Column(
            "created_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "deal_funding",
        sa.Column(
            "updated_by",
            sa.types.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 8. Data migration — rename role values
    op.execute("UPDATE users SET role = 'admin' WHERE role IN ('super_admin', 'org_admin')")
    op.execute("UPDATE users SET role = 'supervisor' WHERE role = 'team_manager'")
    op.execute("UPDATE users SET role = 'regular_user' WHERE role IN ('rep', 'member', 'viewer')")

    # 9. Update users table default
    op.alter_column("users", "role", server_default="regular_user")


def downgrade() -> None:
    # Restore users table default
    op.alter_column("users", "role", server_default="rep")

    # Reverse role data migration
    op.execute("UPDATE users SET role = 'org_admin' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'team_manager' WHERE role = 'supervisor'")
    op.execute("UPDATE users SET role = 'rep' WHERE role = 'regular_user'")

    # Remove authorship columns from deal_funding
    op.drop_column("deal_funding", "updated_by")
    op.drop_column("deal_funding", "created_by")

    # Remove authorship columns from deal_counterparties
    op.drop_column("deal_counterparties", "updated_by")
    op.drop_column("deal_counterparties", "created_by")

    # Remove authorship columns + updated_at from funds
    op.drop_column("funds", "updated_by")
    op.drop_column("funds", "created_by")
    op.drop_column("funds", "updated_at")

    # Remove authorship columns from deals
    op.drop_column("deals", "updated_by")
    op.drop_column("deals", "created_by")

    # Remove authorship columns from companies
    op.drop_column("companies", "updated_by")
    op.drop_column("companies", "created_by")

    # Remove authorship columns from contacts
    op.drop_column("contacts", "updated_by")
    op.drop_column("contacts", "created_by")

    # Remove is_active from teams
    op.drop_column("teams", "is_active")
