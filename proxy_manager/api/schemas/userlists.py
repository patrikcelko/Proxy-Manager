"""
Userlist schemas
================

Request/response schemas for userlists and their entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class UserlistCreate(BaseModel):
    """Payload for creating a new userlist."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""


class UserlistUpdate(BaseModel):
    """Payload for updating an existing userlist."""

    name: str | None = None
    """Unique name identifier."""


class UserlistEntryCreate(BaseModel):
    """Payload for creating a userlist entry."""

    username: str = Field(..., min_length=1, max_length=255)
    """HAProxy userlist username."""

    password: str = Field(..., min_length=1)
    """Plaintext password."""

    sort_order: int = 0
    """Display ordering index."""


class UserlistEntryUpdate(BaseModel):
    """Payload for updating a userlist entry."""

    username: str | None = None
    """HAProxy userlist username."""

    password: str | None = None
    """Plaintext password."""

    sort_order: int | None = None
    """Display ordering index."""


class UserlistEntryResponse(BaseModel):
    """A single userlist entry returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    userlist_id: int
    """Foreign key to the parent userlist."""

    username: str
    """HAProxy userlist username."""

    has_password: bool = True
    """Whether the user has a password set."""

    sort_order: int
    """Display ordering index."""


class UserlistDetailResponse(BaseModel):
    """Userlist with its entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    entries: list[UserlistEntryResponse] = []
    """Child entries."""


class UserlistListResponse(BaseModel):
    """Paginated list of userlists."""

    count: int
    """Total number of items."""

    items: list[UserlistDetailResponse]
    """List of result items."""
