"""
Authentication utilities
========================
"""

import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

_secret_key_cache: str | None = None


def _get_secret_key() -> str:
    """Return the secret key used for JWT encoding/decoding."""

    global _secret_key_cache

    if _secret_key_cache is not None:
        return _secret_key_cache
    secret_key = os.environ.get('PM_SECRET_KEY') or os.environ.get('SECRET_KEY')

    if not secret_key:
        raise RuntimeError('PM_SECRET_KEY environment variable must be set. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"')
    _secret_key_cache = secret_key

    return _secret_key_cache


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""

    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""

    password_bytes = plain_password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')

    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token for a user."""

    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(UTC) + expires_delta
    to_encode = {'sub': str(user_id), 'exp': expire}

    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Decode a JWT access token and return the user ID, or None if invalid."""

    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get('sub')

        if user_id_str is None:
            return None

        return int(user_id_str)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None
