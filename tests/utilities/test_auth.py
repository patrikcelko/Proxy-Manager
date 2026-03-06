"""
Auth utility tests
==================
"""

from proxy_manager.utilities.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify() -> None:
    """Hash and verify."""

    password = "myStrongPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_wrong_password() -> None:
    """Wrong password."""

    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_hash_is_unique() -> None:
    """Hash is unique."""

    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


def test_create_and_decode() -> None:
    """Create and decode."""

    token = create_access_token(42)
    user_id = decode_access_token(token)

    assert user_id == 42


def test_invalid_token() -> None:
    """Invalid token."""

    result = decode_access_token("not.a.valid.token")
    assert result is None


def test_different_users() -> None:
    """Different users."""

    t1 = create_access_token(1)
    t2 = create_access_token(2)

    assert decode_access_token(t1) == 1
    assert decode_access_token(t2) == 2
