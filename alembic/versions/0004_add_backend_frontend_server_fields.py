"""Add new backend, frontend, and server fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-04 01:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('backends', sa.Column('cookie', sa.String(500), nullable=True))
    op.add_column('backends', sa.Column('timeout_server', sa.String(50), nullable=True))
    op.add_column('backends', sa.Column('timeout_connect', sa.String(50), nullable=True))
    op.add_column('backends', sa.Column('timeout_queue', sa.String(50), nullable=True))
    op.add_column('backends', sa.Column('http_check_expect', sa.String(500), nullable=True))
    op.add_column('backends', sa.Column('default_server_options', sa.Text(), nullable=True))
    op.add_column('backends', sa.Column('http_reuse', sa.String(50), nullable=True))
    op.add_column('backends', sa.Column('hash_type', sa.String(100), nullable=True))
    op.add_column('backends', sa.Column('option_httplog', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backends', sa.Column('option_tcplog', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backends', sa.Column('compression_algo', sa.String(100), nullable=True))
    op.add_column('backends', sa.Column('compression_type', sa.String(500), nullable=True))

    op.add_column('backend_servers', sa.Column('weight', sa.Integer(), nullable=True))
    op.add_column('backend_servers', sa.Column('ssl_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backend_servers', sa.Column('ssl_verify', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('backup', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backend_servers', sa.Column('inter', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('fastinter', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('downinter', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('rise', sa.Integer(), nullable=True))
    op.add_column('backend_servers', sa.Column('fall', sa.Integer(), nullable=True))
    op.add_column('backend_servers', sa.Column('cookie_value', sa.String(255), nullable=True))
    op.add_column('backend_servers', sa.Column('send_proxy', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backend_servers', sa.Column('send_proxy_v2', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('backend_servers', sa.Column('slowstart', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('resolve_prefer', sa.String(20), nullable=True))
    op.add_column('backend_servers', sa.Column('resolvers_ref', sa.String(255), nullable=True))
    op.add_column('backend_servers', sa.Column('on_marked_down', sa.String(50), nullable=True))
    op.add_column('backend_servers', sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    op.add_column('frontends', sa.Column('timeout_client', sa.String(50), nullable=True))
    op.add_column('frontends', sa.Column('timeout_http_request', sa.String(50), nullable=True))
    op.add_column('frontends', sa.Column('timeout_http_keep_alive', sa.String(50), nullable=True))
    op.add_column('frontends', sa.Column('maxconn', sa.Integer(), nullable=True))
    op.add_column('frontends', sa.Column('option_httplog', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('frontends', sa.Column('option_tcplog', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('frontends', sa.Column('option_forwardfor', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('frontends', sa.Column('compression_algo', sa.String(100), nullable=True))
    op.add_column('frontends', sa.Column('compression_type', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('frontends', 'compression_type')
    op.drop_column('frontends', 'compression_algo')
    op.drop_column('frontends', 'option_forwardfor')
    op.drop_column('frontends', 'option_tcplog')
    op.drop_column('frontends', 'option_httplog')
    op.drop_column('frontends', 'maxconn')
    op.drop_column('frontends', 'timeout_http_keep_alive')
    op.drop_column('frontends', 'timeout_http_request')
    op.drop_column('frontends', 'timeout_client')

    op.drop_column('backend_servers', 'disabled')
    op.drop_column('backend_servers', 'on_marked_down')
    op.drop_column('backend_servers', 'resolvers_ref')
    op.drop_column('backend_servers', 'resolve_prefer')
    op.drop_column('backend_servers', 'slowstart')
    op.drop_column('backend_servers', 'send_proxy_v2')
    op.drop_column('backend_servers', 'send_proxy')
    op.drop_column('backend_servers', 'cookie_value')
    op.drop_column('backend_servers', 'fall')
    op.drop_column('backend_servers', 'rise')
    op.drop_column('backend_servers', 'downinter')
    op.drop_column('backend_servers', 'fastinter')
    op.drop_column('backend_servers', 'inter')
    op.drop_column('backend_servers', 'backup')
    op.drop_column('backend_servers', 'ssl_verify')
    op.drop_column('backend_servers', 'ssl_enabled')
    op.drop_column('backend_servers', 'weight')

    op.drop_column('backends', 'compression_type')
    op.drop_column('backends', 'compression_algo')
    op.drop_column('backends', 'option_tcplog')
    op.drop_column('backends', 'option_httplog')
    op.drop_column('backends', 'hash_type')
    op.drop_column('backends', 'http_reuse')
    op.drop_column('backends', 'default_server_options')
    op.drop_column('backends', 'http_check_expect')
    op.drop_column('backends', 'timeout_queue')
    op.drop_column('backends', 'timeout_connect')
    op.drop_column('backends', 'timeout_server')
    op.drop_column('backends', 'cookie')
