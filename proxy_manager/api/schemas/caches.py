"""
Cache schemas
=============

Request/response schemas for cache sections.
"""

from pydantic import BaseModel, ConfigDict, Field


class CacheSectionCreate(BaseModel):
    """Payload for creating a new cache section."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    total_max_size: int | None = None
    """Total cache size in megabytes."""

    max_object_size: int | None = None
    """Maximum cached object size in bytes."""

    max_age: int | None = None
    """Maximum cache entry age in seconds."""

    max_secondary_entries: int | None = None
    """Maximum number of secondary entries."""

    process_vary: int | None = None
    """Process Vary header (1 = enabled)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class CacheSectionUpdate(BaseModel):
    """Payload for updating an existing cache section."""

    name: str | None = None
    """Unique name identifier."""

    total_max_size: int | None = None
    """Total cache size in megabytes."""

    max_object_size: int | None = None
    """Maximum cached object size in bytes."""

    max_age: int | None = None
    """Maximum cache entry age in seconds."""

    max_secondary_entries: int | None = None
    """Maximum number of secondary entries."""

    process_vary: int | None = None
    """Process Vary header (1 = enabled)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class CacheSectionResponse(BaseModel):
    """A single cache section returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    total_max_size: int | None
    """Total cache size in megabytes."""

    max_object_size: int | None
    """Maximum cached object size in bytes."""

    max_age: int | None
    """Maximum cache entry age in seconds."""

    max_secondary_entries: int | None
    """Maximum number of secondary entries."""

    process_vary: int | None
    """Process Vary header (1 = enabled)."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None
    """Additional HAProxy directives (free-form text)."""


class CacheSectionListResponse(BaseModel):
    """Paginated list of cache sections."""

    count: int
    """Total number of items."""

    items: list[CacheSectionResponse]
    """List of result items."""
