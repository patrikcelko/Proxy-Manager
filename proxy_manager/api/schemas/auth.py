"""
Auth schemas
============
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserLoginRequest(BaseModel):
    """Login credentials payload."""

    email: str = Field(..., examples=["admin@example.com"])
    """Unique email address."""

    password: str = Field(..., min_length=4)
    """Plaintext password."""


class UserRegisterRequest(BaseModel):
    """Registration payload with name, email, and password."""

    email: str = Field(..., examples=["admin@example.com"])
    """Unique email address."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    password: str = Field(..., min_length=6)
    """Plaintext password."""


class UserResponse(BaseModel):
    """Public user profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    """Primary key."""

    email: str
    """Unique email address."""

    name: str
    """Unique name identifier."""

    created_at: datetime.datetime
    """Record creation timestamp."""


class TokenResponse(BaseModel):
    """JWT token response after successful authentication."""

    access_token: str
    """JWT access token."""

    token_type: str = "bearer"  # noqa: S105
    """Token type (always `bearer`)."""

    user: UserResponse
    """Authenticated user details."""


class ProfileUpdateRequest(BaseModel):
    """Payload for updating user profile fields."""

    email: str | None = None
    """Unique email address."""

    name: str | None = None
    """Unique name identifier."""

    current_password: str | None = None
    """Current password for verification."""

    new_password: str | None = None
    """New password to set."""
