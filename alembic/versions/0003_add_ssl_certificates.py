"""Add ssl_certificates table

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-04 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ssl_certificates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("domain", sa.String(255), nullable=False, unique=True),
        sa.Column("alt_domains", sa.Text(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="certbot"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("cert_path", sa.String(500), nullable=True),
        sa.Column("key_path", sa.String(500), nullable=True),
        sa.Column("fullchain_path", sa.String(500), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("challenge_type", sa.String(50), nullable=False, server_default="http-01"),
        sa.Column("dns_plugin", sa.String(100), nullable=True),
        sa.Column("last_renewal_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ssl_certificates")
