"""Add SMTP auth fields to mailer entries

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0010'
down_revision: str | None = '0009'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('mailer_entries', sa.Column('smtp_auth', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('mailer_entries', sa.Column('smtp_user', sa.String(255), nullable=True))
    op.add_column('mailer_entries', sa.Column('smtp_password', sa.String(500), nullable=True))
    op.add_column('mailer_entries', sa.Column('use_tls', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('mailer_entries', sa.Column('use_starttls', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('mailer_entries', 'use_starttls')
    op.drop_column('mailer_entries', 'use_tls')
    op.drop_column('mailer_entries', 'smtp_password')
    op.drop_column('mailer_entries', 'smtp_user')
    op.drop_column('mailer_entries', 'smtp_auth')
