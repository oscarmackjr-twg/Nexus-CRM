"""contact_pe_fields — add PE Blueprint columns to contacts table"""

from alembic import op
import sqlalchemy as sa

revision = "0003_contact_pe_fields"
down_revision = "0002_pe_ref_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phone fields (CONTACT-01)
    op.add_column("contacts", sa.Column("business_phone", sa.String(50), nullable=True))
    op.add_column("contacts", sa.Column("mobile_phone", sa.String(50), nullable=True))
    op.add_column("contacts", sa.Column("assistant_name", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("assistant_email", sa.String(255), nullable=True))
    op.add_column("contacts", sa.Column("assistant_phone", sa.String(50), nullable=True))

    # Address fields (CONTACT-02)
    op.add_column("contacts", sa.Column("address", sa.Text, nullable=True))
    op.add_column("contacts", sa.Column("city", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("state", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("postal_code", sa.String(20), nullable=True))
    op.add_column("contacts", sa.Column("country", sa.String(100), nullable=True))

    # FK + scalar fields (CONTACT-03)
    op.add_column(
        "contacts",
        sa.Column(
            "contact_type_id",
            sa.String(36),
            sa.ForeignKey("ref_data.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("contacts", sa.Column("primary_contact", sa.Boolean, nullable=True))
    op.add_column("contacts", sa.Column("contact_frequency", sa.Integer, nullable=True))

    # JSONB fields (CONTACT-05, CONTACT-06)
    op.add_column("contacts", sa.Column("sector", sa.JSON(none_as_null=True), nullable=True))
    op.add_column("contacts", sa.Column("sub_sector", sa.JSON(none_as_null=True), nullable=True))
    op.add_column("contacts", sa.Column("previous_employment", sa.JSON(none_as_null=True), nullable=True))
    op.add_column("contacts", sa.Column("board_memberships", sa.JSON(none_as_null=True), nullable=True))

    # Text + indexed fields (CONTACT-07)
    op.add_column("contacts", sa.Column("linkedin_url", sa.Text, nullable=True))
    op.add_column("contacts", sa.Column("legacy_id", sa.String(100), nullable=True))

    # Unique constraint for org-scoped legacy_id
    op.create_unique_constraint(
        "uq_contacts_org_legacy_id", "contacts", ["org_id", "legacy_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_contacts_org_legacy_id", "contacts", type_="unique")
    op.drop_column("contacts", "legacy_id")
    op.drop_column("contacts", "linkedin_url")
    op.drop_column("contacts", "board_memberships")
    op.drop_column("contacts", "previous_employment")
    op.drop_column("contacts", "sub_sector")
    op.drop_column("contacts", "sector")
    op.drop_column("contacts", "contact_frequency")
    op.drop_column("contacts", "primary_contact")
    op.drop_column("contacts", "contact_type_id")
    op.drop_column("contacts", "country")
    op.drop_column("contacts", "postal_code")
    op.drop_column("contacts", "state")
    op.drop_column("contacts", "city")
    op.drop_column("contacts", "address")
    op.drop_column("contacts", "assistant_phone")
    op.drop_column("contacts", "assistant_email")
    op.drop_column("contacts", "assistant_name")
    op.drop_column("contacts", "mobile_phone")
    op.drop_column("contacts", "business_phone")
