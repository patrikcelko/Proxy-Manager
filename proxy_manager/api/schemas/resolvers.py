"""
Resolver schemas
================

Request/response schemas for resolvers and their nameserver entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class ResolverNameserverCreate(BaseModel):
    """Payload for creating a resolver nameserver."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    address: str = Field(..., min_length=1)
    """Server IP address or hostname."""

    port: int = Field(default=53, ge=1, le=65535)
    """Server port number."""

    sort_order: int = 0
    """Display ordering index."""


class ResolverNameserverUpdate(BaseModel):
    """Payload for updating a resolver nameserver."""

    name: str | None = None
    """Unique name identifier."""

    address: str | None = None
    """Server IP address or hostname."""

    port: int | None = Field(default=None, ge=1, le=65535)
    """Server port number."""

    sort_order: int | None = None
    """Display ordering index."""


class ResolverNameserverResponse(BaseModel):
    """A single resolver nameserver returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    resolver_id: int
    """Foreign key to the parent resolver."""

    name: str
    """Unique name identifier."""

    address: str
    """Server IP address or hostname."""

    port: int
    """Server port number."""

    sort_order: int
    """Display ordering index."""


class ResolverCreate(BaseModel):
    """Payload for creating a new resolver section."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    resolve_retries: int | None = None
    """Number of DNS resolution retries."""

    timeout_resolve: str | None = None
    """DNS resolution timeout."""

    timeout_retry: str | None = None
    """DNS retry timeout."""

    hold_valid: str | None = None
    """Hold time for valid DNS responses."""

    hold_other: str | None = None
    """Hold time for other DNS response codes."""

    hold_refused: str | None = None
    """Hold time for refused DNS responses."""

    hold_timeout: str | None = None
    """Hold time for DNS timeouts."""

    hold_obsolete: str | None = None
    """Hold time for obsolete DNS entries."""

    hold_nx: str | None = None
    """Hold time for NXDOMAIN responses."""

    hold_aa: str | None = None
    """Hold time for authoritative answers."""

    accepted_payload_size: int | None = None
    """Maximum accepted DNS payload size in bytes."""

    parse_resolv_conf: int | None = None
    """Parse `/etc/resolv.conf` (1 = enabled)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class ResolverUpdate(BaseModel):
    """Payload for updating an existing resolver section."""

    name: str | None = None
    """Unique name identifier."""

    resolve_retries: int | None = None
    """Number of DNS resolution retries."""

    timeout_resolve: str | None = None
    """DNS resolution timeout."""

    timeout_retry: str | None = None
    """DNS retry timeout."""

    hold_valid: str | None = None
    """Hold time for valid DNS responses."""

    hold_other: str | None = None
    """Hold time for other DNS response codes."""

    hold_refused: str | None = None
    """Hold time for refused DNS responses."""

    hold_timeout: str | None = None
    """Hold time for DNS timeouts."""

    hold_obsolete: str | None = None
    """Hold time for obsolete DNS entries."""

    hold_nx: str | None = None
    """Hold time for NXDOMAIN responses."""

    hold_aa: str | None = None
    """Hold time for authoritative answers."""

    accepted_payload_size: int | None = None
    """Maximum accepted DNS payload size in bytes."""

    parse_resolv_conf: int | None = None
    """Parse `/etc/resolv.conf` (1 = enabled)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class ResolverDetailResponse(BaseModel):
    """Resolver section with its nameserver entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    resolve_retries: int | None
    """Number of DNS resolution retries."""

    timeout_resolve: str | None
    """DNS resolution timeout."""

    timeout_retry: str | None
    """DNS retry timeout."""

    hold_valid: str | None
    """Hold time for valid DNS responses."""

    hold_other: str | None
    """Hold time for other DNS response codes."""

    hold_refused: str | None
    """Hold time for refused DNS responses."""

    hold_timeout: str | None
    """Hold time for DNS timeouts."""

    hold_obsolete: str | None
    """Hold time for obsolete DNS entries."""

    hold_nx: str | None = None
    """Hold time for NXDOMAIN responses."""

    hold_aa: str | None = None
    """Hold time for authoritative answers."""

    accepted_payload_size: int | None
    """Maximum accepted DNS payload size in bytes."""

    parse_resolv_conf: int | None = None
    """Parse `/etc/resolv.conf` (1 = enabled)."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None
    """Additional HAProxy directives (free-form text)."""

    nameservers: list[ResolverNameserverResponse] = []
    """Nameserver entries."""


class ResolverListResponse(BaseModel):
    """Paginated list of resolver sections."""

    count: int
    """Total number of items."""

    items: list[ResolverDetailResponse]
    """List of result items."""
