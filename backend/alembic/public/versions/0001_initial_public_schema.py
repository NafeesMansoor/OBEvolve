"""initial public schema: institutions, platform_admins

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("schema_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="trial"),
        sa.Column("subscription_plan", sa.String(50), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_institutions_code"),
        sa.UniqueConstraint("slug", name="uq_institutions_slug"),
        sa.UniqueConstraint("schema_name", name="uq_institutions_schema_name"),
        schema="public",
    )
    op.create_index("ix_institutions_slug", "institutions", ["slug"], schema="public")

    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_platform_admins_email"),
        schema="public",
    )
    op.create_index("ix_platform_admins_email", "platform_admins", ["email"], schema="public")


def downgrade() -> None:
    op.drop_index("ix_platform_admins_email", table_name="platform_admins", schema="public")
    op.drop_table("platform_admins", schema="public")
    op.drop_index("ix_institutions_slug", table_name="institutions", schema="public")
    op.drop_table("institutions", schema="public")
