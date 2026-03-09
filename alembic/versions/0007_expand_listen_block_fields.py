"""Expand listen_blocks with structured fields

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0007'
down_revision: str | None = '0006'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('listen_blocks', sa.Column('balance', sa.String(100), nullable=True))
    op.add_column('listen_blocks', sa.Column('maxconn', sa.Integer(), nullable=True))
    op.add_column('listen_blocks', sa.Column('timeout_client', sa.String(100), nullable=True))
    op.add_column('listen_blocks', sa.Column('timeout_server', sa.String(100), nullable=True))
    op.add_column('listen_blocks', sa.Column('timeout_connect', sa.String(100), nullable=True))
    op.add_column('listen_blocks', sa.Column('default_server_params', sa.Text(), nullable=True))
    op.add_column('listen_blocks', sa.Column('option_httplog', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('listen_blocks', sa.Column('option_tcplog', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('listen_blocks', sa.Column('option_forwardfor', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('listen_blocks', 'option_forwardfor')
    op.drop_column('listen_blocks', 'option_tcplog')
    op.drop_column('listen_blocks', 'option_httplog')
    op.drop_column('listen_blocks', 'default_server_params')
    op.drop_column('listen_blocks', 'timeout_connect')
    op.drop_column('listen_blocks', 'timeout_server')
    op.drop_column('listen_blocks', 'timeout_client')
    op.drop_column('listen_blocks', 'maxconn')
    op.drop_column('listen_blocks', 'balance')
