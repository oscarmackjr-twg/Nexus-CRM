"""contact_coverage_persons — M2M association table for coverage persons"""

from alembic import op
import sqlalchemy as sa

revision = "0004_contact_coverage_persons"
down_revision = "0003_contact_pe_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contact_coverage_persons",
        sa.Column(
            "contact_id",
            sa.Uuid(),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("contact_id", "user_id", name="pk_contact_coverage_persons"),
    )


def downgrade() -> None:
    op.drop_table("contact_coverage_persons")
