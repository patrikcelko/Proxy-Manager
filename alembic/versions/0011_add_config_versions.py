"""Add config_versions table

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0011'
down_revision: str | None = '0010'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'config_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=False, server_default=''),
        sa.Column('snapshot', sa.Text(), nullable=False),
        sa.Column('parent_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('config_versions')
