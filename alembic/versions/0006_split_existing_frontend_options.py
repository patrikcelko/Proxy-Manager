"""Split existing frontend_options directive into directive + value

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, directive, value FROM frontend_options WHERE value = '' OR value IS NULL")).fetchall()

    for row in rows:
        directive = row[1] or ""
        parts = directive.split(None, 1)

        if len(parts) == 2:
            conn.execute(
                sa.text("UPDATE frontend_options SET directive = :d, value = :v WHERE id = :id"),
                {"d": parts[0], "v": parts[1], "id": row[0]},
            )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, directive, value FROM frontend_options WHERE value != '' AND value IS NOT NULL")).fetchall()

    for row in rows:
        combined = f"{row[1]} {row[2]}".strip()
        conn.execute(
            sa.text("UPDATE frontend_options SET directive = :d, value = '' WHERE id = :id"),
            {"d": combined, "id": row[0]},
        )
