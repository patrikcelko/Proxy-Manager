"""Add unique constraints and schema fixes

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_backend_server_name", "backend_servers", ["backend_id", "name"])
    op.create_unique_constraint("uq_userlist_entry_username", "userlist_entries", ["userlist_id", "username"])
    op.create_unique_constraint("uq_resolver_nameserver_name", "resolver_nameservers", ["resolver_id", "name"])
    op.create_unique_constraint("uq_peer_entry_name", "peer_entries", ["peer_section_id", "name"])
    op.create_unique_constraint("uq_mailer_entry_name", "mailer_entries", ["mailer_section_id", "name"])

    op.alter_column("config_versions", "user_id", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint("config_versions_user_id_fkey", "config_versions", type_="foreignkey")
    op.create_foreign_key("config_versions_user_id_fkey", "config_versions", "users", ["user_id"], ["id"], ondelete="SET NULL")

    op.alter_column("ssl_certificates", "issued_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True))
    op.alter_column("ssl_certificates", "expires_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True))
    op.alter_column("ssl_certificates", "last_renewal_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True))
    op.alter_column("ssl_certificates", "created_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True))
    op.alter_column("ssl_certificates", "updated_at", existing_type=sa.DateTime(), type_=sa.DateTime(timezone=True))


def downgrade() -> None:
    op.alter_column("ssl_certificates", "updated_at", existing_type=sa.DateTime(timezone=True), type_=sa.DateTime())
    op.alter_column("ssl_certificates", "created_at", existing_type=sa.DateTime(timezone=True), type_=sa.DateTime())
    op.alter_column("ssl_certificates", "last_renewal_at", existing_type=sa.DateTime(timezone=True), type_=sa.DateTime())
    op.alter_column("ssl_certificates", "expires_at", existing_type=sa.DateTime(timezone=True), type_=sa.DateTime())
    op.alter_column("ssl_certificates", "issued_at", existing_type=sa.DateTime(timezone=True), type_=sa.DateTime())

    op.drop_constraint("config_versions_user_id_fkey", "config_versions", type_="foreignkey")
    op.create_foreign_key("config_versions_user_id_fkey", "config_versions", "users", ["user_id"], ["id"])
    op.alter_column("config_versions", "user_id", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint("uq_mailer_entry_name", "mailer_entries", type_="unique")
    op.drop_constraint("uq_peer_entry_name", "peer_entries", type_="unique")
    op.drop_constraint("uq_resolver_nameserver_name", "resolver_nameservers", type_="unique")
    op.drop_constraint("uq_userlist_entry_username", "userlist_entries", type_="unique")
    op.drop_constraint("uq_backend_server_name", "backend_servers", type_="unique")
