"""Expand resolver, peer, mailer, http-errors sections

Revision ID: 0009
Revises: 0008
Create Date: 2025-06-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0009'
down_revision: str | None = '0008'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('resolvers', sa.Column('hold_nx', sa.String(50), nullable=True))
    op.add_column('resolvers', sa.Column('hold_aa', sa.String(50), nullable=True))
    op.add_column('resolvers', sa.Column('parse_resolv_conf', sa.Integer(), nullable=True))

    op.add_column('peer_sections', sa.Column('default_bind', sa.Text(), nullable=True))
    op.add_column('peer_sections', sa.Column('default_server_options', sa.Text(), nullable=True))

    op.add_column('mailer_sections', sa.Column('extra_options', sa.Text(), nullable=True))

    op.add_column('http_errors_sections', sa.Column('extra_options', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('http_errors_sections', 'extra_options')
    op.drop_column('mailer_sections', 'extra_options')
    op.drop_column('peer_sections', 'default_server_options')
    op.drop_column('peer_sections', 'default_bind')
    op.drop_column('resolvers', 'parse_resolv_conf')
    op.drop_column('resolvers', 'hold_aa')
    op.drop_column('resolvers', 'hold_nx')
