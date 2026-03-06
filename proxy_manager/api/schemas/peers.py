"""
Peer schemas
============

Request/response schemas for peer sections and their entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class PeerEntryCreate(BaseModel):
    """Payload for creating a peer entry."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    address: str = Field(..., min_length=1)
    """Server IP address or hostname."""

    port: int = Field(default=10000, ge=1, le=65535)
    """Server port number."""

    sort_order: int = 0
    """Display ordering index."""


class PeerEntryUpdate(BaseModel):
    """Payload for updating a peer entry."""

    name: str | None = None
    """Unique name identifier."""

    address: str | None = None
    """Server IP address or hostname."""

    port: int | None = None
    """Server port number."""

    sort_order: int | None = None
    """Display ordering index."""


class PeerEntryResponse(BaseModel):
    """A single peer entry returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    peer_section_id: int
    """Foreign key to the parent peer section."""

    name: str
    """Unique name identifier."""

    address: str
    """Server IP address or hostname."""

    port: int
    """Server port number."""

    sort_order: int
    """Display ordering index."""


class PeerSectionCreate(BaseModel):
    """Payload for creating a new peer section."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    default_bind: str | None = None
    """Default bind address for peer connections."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""


class PeerSectionUpdate(BaseModel):
    """Payload for updating an existing peer section."""

    name: str | None = None
    """Unique name identifier."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    default_bind: str | None = None
    """Default bind address for peer connections."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""


class PeerSectionDetailResponse(BaseModel):
    """Peer section with its peer entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None
    """Additional HAProxy directives (free-form text)."""

    default_bind: str | None = None
    """Default bind address for peer connections."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""

    entries: list[PeerEntryResponse] = []
    """Child entries."""


class PeerSectionListResponse(BaseModel):
    """Paginated list of peer sections."""

    count: int
    """Total number of items."""

    items: list[PeerSectionDetailResponse]
    """List of result items."""
