"""
Settings schemas
================

Request/response schemas for global and default settings.
"""

from pydantic import BaseModel, ConfigDict, Field


class SettingCreate(BaseModel):
    """Payload for creating a global or default setting."""

    directive: str = Field(..., min_length=1, max_length=255)
    """HAProxy directive name."""

    value: str = Field(default='')
    """Directive value."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int = 0
    """Display ordering index."""


class SettingUpdate(BaseModel):
    """Payload for updating a global or default setting."""

    directive: str | None = None
    """HAProxy directive name."""

    value: str | None = None
    """Directive value."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int | None = None
    """Display ordering index."""


class SettingResponse(BaseModel):
    """A single setting entry returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    directive: str
    """HAProxy directive name."""

    value: str
    """Directive value."""

    comment: str | None
    """Optional user comment."""

    sort_order: int
    """Display ordering index."""


class SettingListResponse(BaseModel):
    """Paginated list of settings."""

    count: int
    """Total number of items."""

    items: list[SettingResponse]
    """List of result items."""
