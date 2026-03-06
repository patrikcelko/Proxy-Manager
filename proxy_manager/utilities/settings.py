"""
Settings
========
"""

import os


def _get_env(key: str, default: str) -> str:
    """Return environment variable value or default."""

    return os.environ.get(key, default)


DATABASE_URL: str = _get_env(
    "DATABASE_URL",
    "postgresql+asyncpg://proxy_manager:proxy_manager@localhost:5432/proxy_manager",
)

DATABASE_URL_SYNC: str = _get_env(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://proxy_manager:proxy_manager@localhost:5432/proxy_manager",
)
