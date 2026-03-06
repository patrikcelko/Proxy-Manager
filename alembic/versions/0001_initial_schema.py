"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "global_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("directive", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "default_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("directive", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "userlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
    )
    op.create_table(
        "userlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("userlist_id", sa.Integer(), sa.ForeignKey("userlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "frontends",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("default_backend", sa.String(255), nullable=True),
        sa.Column("mode", sa.String(50), server_default="http"),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_table(
        "frontend_binds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("frontend_id", sa.Integer(), sa.ForeignKey("frontends.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bind_line", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )
    op.create_table(
        "frontend_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("frontend_id", sa.Integer(), sa.ForeignKey("frontends.id", ondelete="CASCADE"), nullable=False),
        sa.Column("directive", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "acl_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("frontend_id", sa.Integer(), sa.ForeignKey("frontends.id", ondelete="CASCADE"), nullable=True),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("backend_name", sa.String(255), nullable=True),
        sa.Column("acl_match_type", sa.String(50), server_default="hdr"),
        sa.Column("is_redirect", sa.Boolean(), server_default="false"),
        sa.Column("redirect_target", sa.Text(), nullable=True),
        sa.Column("redirect_code", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
    )

    op.create_table(
        "backends",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("mode", sa.String(50), nullable=True),
        sa.Column("balance", sa.String(100), nullable=True),
        sa.Column("option_forwardfor", sa.Boolean(), server_default="false"),
        sa.Column("option_redispatch", sa.Boolean(), server_default="false"),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column("retry_on", sa.String(255), nullable=True),
        sa.Column("auth_userlist", sa.String(255), nullable=True),
        sa.Column("health_check_enabled", sa.Boolean(), server_default="false"),
        sa.Column("health_check_method", sa.String(50), nullable=True),
        sa.Column("health_check_uri", sa.Text(), nullable=True),
        sa.Column("errorfile", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("extra_options", sa.Text(), nullable=True),
    )
    op.create_table(
        "backend_servers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backend_id", sa.Integer(), sa.ForeignKey("backends.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("check_enabled", sa.Boolean(), server_default="true"),
        sa.Column("maxconn", sa.Integer(), nullable=True),
        sa.Column("maxqueue", sa.Integer(), nullable=True),
        sa.Column("extra_params", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "listen_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("bind_address", sa.String(255), nullable=True),
        sa.Column("mode", sa.String(50), server_default="http"),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("listen_blocks")
    op.drop_table("backend_servers")
    op.drop_table("backends")
    op.drop_table("acl_rules")
    op.drop_table("frontend_options")
    op.drop_table("frontend_binds")
    op.drop_table("frontends")
    op.drop_table("userlist_entries")
    op.drop_table("userlists")
    op.drop_table("default_settings")
    op.drop_table("global_settings")
    op.drop_table("users")
