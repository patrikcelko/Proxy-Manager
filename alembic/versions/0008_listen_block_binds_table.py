"""Create listen_block_binds child table, migrate existing bind_address
data and drop bind_address column from listen_blocks.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0008'
down_revision: str | None = '0007'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'listen_block_binds',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'listen_block_id',
            sa.Integer(),
            sa.ForeignKey('listen_blocks.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('bind_line', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # Migrate existing bind_address data into bind rows
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, bind_address FROM listen_blocks WHERE bind_address IS NOT NULL AND bind_address != ''")).fetchall()
    for row in rows:
        conn.execute(
            sa.text('INSERT INTO listen_block_binds (listen_block_id, bind_line, sort_order) VALUES (:lid, :bl, 0)'),
            {'lid': row[0], 'bl': row[1]},
        )

    op.drop_column('listen_blocks', 'bind_address')


def downgrade() -> None:
    op.add_column(
        'listen_blocks',
        sa.Column('bind_address', sa.Text(), nullable=False, server_default=''),
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text('SELECT DISTINCT ON (listen_block_id) listen_block_id, bind_line FROM listen_block_binds ORDER BY listen_block_id, sort_order, id')).fetchall()
    for row in rows:
        conn.execute(
            sa.text('UPDATE listen_blocks SET bind_address = :bl WHERE id = :lid'),
            {'lid': row[0], 'bl': row[1]},
        )

    op.drop_table('listen_block_binds')
