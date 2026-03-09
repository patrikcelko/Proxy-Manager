"""Add value and comment columns to frontend_options

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('frontend_options', sa.Column('value', sa.Text(), nullable=False, server_default=''))
    op.add_column('frontend_options', sa.Column('comment', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('frontend_options', 'comment')
    op.drop_column('frontend_options', 'value')
