"""Add resolvers, peers, mailers, http-errors, cache

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'resolvers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('resolve_retries', sa.Integer(), nullable=True),
        sa.Column('timeout_resolve', sa.String(50), nullable=True),
        sa.Column('timeout_retry', sa.String(50), nullable=True),
        sa.Column('hold_valid', sa.String(50), nullable=True),
        sa.Column('hold_other', sa.String(50), nullable=True),
        sa.Column('hold_refused', sa.String(50), nullable=True),
        sa.Column('hold_timeout', sa.String(50), nullable=True),
        sa.Column('hold_obsolete', sa.String(50), nullable=True),
        sa.Column('accepted_payload_size', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('extra_options', sa.Text(), nullable=True),
    )
    op.create_table(
        'resolver_nameservers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('resolver_id', sa.Integer(), sa.ForeignKey('resolvers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='53'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'peer_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('extra_options', sa.Text(), nullable=True),
    )
    op.create_table(
        'peer_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'peer_section_id',
            sa.Integer(),
            sa.ForeignKey('peer_sections.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'mailer_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('timeout_mail', sa.String(50), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
    )
    op.create_table(
        'mailer_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'mailer_section_id',
            sa.Integer(),
            sa.ForeignKey('mailer_sections.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'http_errors_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('comment', sa.Text(), nullable=True),
    )
    op.create_table(
        'http_error_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            'section_id',
            sa.Integer(),
            sa.ForeignKey('http_errors_sections.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, server_default='errorfile'),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'cache_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('total_max_size', sa.Integer(), nullable=True),
        sa.Column('max_object_size', sa.Integer(), nullable=True),
        sa.Column('max_age', sa.Integer(), nullable=True),
        sa.Column('max_secondary_entries', sa.Integer(), nullable=True),
        sa.Column('process_vary', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('extra_options', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('cache_sections')
    op.drop_table('http_error_entries')
    op.drop_table('http_errors_sections')
    op.drop_table('mailer_entries')
    op.drop_table('mailer_sections')
    op.drop_table('peer_entries')
    op.drop_table('peer_sections')
    op.drop_table('resolver_nameservers')
    op.drop_table('resolvers')
