"""
Listen block schemas
====================

Request/response schemas for listen blocks and their bind entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class ListenBlockCreate(BaseModel):
    """Payload for creating a new listen block."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    mode: str = "http"
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None = None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    default_server_params: str | None = None
    """Default server parameters applied to all servers."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool = False
    """Enable `option forwardfor` (X-Forwarded-For)."""

    content: str | None = None
    """Raw configuration content."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int = 0
    """Display ordering index."""


class ListenBlockUpdate(BaseModel):
    """Payload for updating an existing listen block."""

    name: str | None = None
    """Unique name identifier."""

    mode: str | None = Field(default=None, pattern=r"^(http|tcp)$")
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None = None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    default_server_params: str | None = None
    """Default server parameters applied to all servers."""

    option_httplog: bool | None = None
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool | None = None
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool | None = None
    """Enable `option forwardfor` (X-Forwarded-For)."""

    content: str | None = None
    """Raw configuration content."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int | None = None
    """Display ordering index."""


class ListenBlockBindCreate(BaseModel):
    """Payload for creating a listen block bind."""

    bind_line: str = Field(..., min_length=1)
    """Full bind directive (address, port, options)."""

    sort_order: int = 0
    """Display ordering index."""


class ListenBlockBindUpdate(BaseModel):
    """Payload for updating a listen block bind."""

    bind_line: str | None = None
    """Full bind directive (address, port, options)."""

    sort_order: int | None = None
    """Display ordering index."""


class ListenBlockBindResponse(BaseModel):
    """A single listen block bind returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    listen_block_id: int
    """Foreign key to the parent listen block."""

    bind_line: str
    """Full bind directive (address, port, options)."""

    sort_order: int
    """Display ordering index."""


class ListenBlockDetailResponse(BaseModel):
    """Listen block with its bind entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    mode: str
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None = None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    default_server_params: str | None = None
    """Default server parameters applied to all servers."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool = False
    """Enable `option forwardfor` (X-Forwarded-For)."""

    content: str | None
    """Raw configuration content."""

    comment: str | None
    """Optional user comment."""

    sort_order: int
    """Display ordering index."""

    binds: list[ListenBlockBindResponse] = []
    """Bind directives."""


class ListenBlockListResponse(BaseModel):
    """Paginated list of listen blocks."""

    count: int
    """Total number of items."""

    items: list[ListenBlockDetailResponse]
    """List of result items."""
