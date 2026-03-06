"""
HTTP errors schemas
===================

Request/response schemas for http-errors sections and their entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class HttpErrorEntryCreate(BaseModel):
    """Payload for creating an HTTP error entry."""

    status_code: int = Field(..., ge=100, le=599)
    """HTTP status code."""

    type: str = Field(default="errorfile", pattern=r"^(errorfile|errorloc|errorloc302|errorloc303)$")
    """Error response type (`errorfile`, `errorloc`, etc.)."""

    value: str = Field(..., min_length=1)
    """Directive value."""

    sort_order: int = 0
    """Display ordering index."""


class HttpErrorEntryUpdate(BaseModel):
    """Payload for updating an HTTP error entry."""

    status_code: int | None = None
    """HTTP status code."""

    type: str | None = None
    """Error response type (`errorfile`, `errorloc`, etc.)."""

    value: str | None = None
    """Directive value."""

    sort_order: int | None = None
    """Display ordering index."""


class HttpErrorEntryResponse(BaseModel):
    """A single HTTP error entry returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    section_id: int
    """Foreign key to the parent http-errors section."""

    status_code: int
    """HTTP status code."""

    type: str
    """Error response type (`errorfile`, `errorloc`, etc.)."""

    value: str
    """Directive value."""

    sort_order: int
    """Display ordering index."""


class HttpErrorsSectionCreate(BaseModel):
    """Payload for creating a new HTTP errors section."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class HttpErrorsSectionUpdate(BaseModel):
    """Payload for updating an existing HTTP errors section."""

    name: str | None = None
    """Unique name identifier."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class HttpErrorsSectionDetailResponse(BaseModel):
    """HTTP errors section with its entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    entries: list[HttpErrorEntryResponse] = []
    """Child entries."""


class HttpErrorsSectionListResponse(BaseModel):
    """Paginated list of HTTP errors sections."""

    count: int
    """Total number of items."""

    items: list[HttpErrorsSectionDetailResponse]
    """List of result items."""
