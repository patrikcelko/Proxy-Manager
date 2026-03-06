"""
Frontend schemas
================

Request/response schemas for frontends, binds, options, and ACL rules.
"""

from pydantic import BaseModel, ConfigDict, Field


class FrontendCreate(BaseModel):
    """Payload for creating a new frontend."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    default_backend: str | None = None
    """Default backend when no ACL matches."""

    mode: str = "http"
    """Proxy mode (`http` or `tcp`)."""

    comment: str | None = None
    """Optional user comment."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_http_request: str | None = None
    """Timeout for receiving the HTTP request."""

    timeout_http_keep_alive: str | None = None
    """Timeout for HTTP keep-alive connections."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool = False
    """Enable `option forwardfor` (X-Forwarded-For)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""


class FrontendUpdate(BaseModel):
    """Payload for updating an existing frontend."""

    name: str | None = None
    """Unique name identifier."""

    default_backend: str | None = None
    """Default backend when no ACL matches."""

    mode: str | None = None
    """Proxy mode (`http` or `tcp`)."""

    comment: str | None = None
    """Optional user comment."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_http_request: str | None = None
    """Timeout for receiving the HTTP request."""

    timeout_http_keep_alive: str | None = None
    """Timeout for HTTP keep-alive connections."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    option_httplog: bool | None = None
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool | None = None
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool | None = None
    """Enable `option forwardfor` (X-Forwarded-For)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""


class FrontendBindCreate(BaseModel):
    """Payload for creating a frontend bind."""

    bind_line: str = Field(..., min_length=1)
    """Full bind directive (address, port, options)."""

    sort_order: int = 0
    """Display ordering index."""


class FrontendBindUpdate(BaseModel):
    """Payload for updating a frontend bind."""

    bind_line: str | None = None
    """Full bind directive (address, port, options)."""

    sort_order: int | None = None
    """Display ordering index."""


class FrontendBindResponse(BaseModel):
    """A single frontend bind returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    frontend_id: int
    """Foreign key to the parent frontend."""

    bind_line: str
    """Full bind directive (address, port, options)."""

    sort_order: int
    """Display ordering index."""


class FrontendOptionCreate(BaseModel):
    """Payload for creating a frontend option."""

    directive: str = Field(..., min_length=1)
    """HAProxy directive name."""

    value: str = ""
    """Directive value."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int = 0
    """Display ordering index."""


class FrontendOptionUpdate(BaseModel):
    """Payload for updating a frontend option."""

    directive: str | None = None
    """HAProxy directive name."""

    value: str | None = None
    """Directive value."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int | None = None
    """Display ordering index."""


class FrontendOptionResponse(BaseModel):
    """A single frontend option returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    frontend_id: int
    """Foreign key to the parent frontend."""

    directive: str
    """HAProxy directive name."""

    value: str
    """Directive value."""

    comment: str | None
    """Optional user comment."""

    sort_order: int
    """Display ordering index."""


class FrontendDetailResponse(BaseModel):
    """Frontend with binds, options, and ACL rules."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    default_backend: str | None
    """Default backend when no ACL matches."""

    mode: str
    """Proxy mode (`http` or `tcp`)."""

    comment: str | None
    """Optional user comment."""

    timeout_client: str | None = None
    """Client-side timeout."""

    timeout_http_request: str | None = None
    """Timeout for receiving the HTTP request."""

    timeout_http_keep_alive: str | None = None
    """Timeout for HTTP keep-alive connections."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: bool = False
    """Enable `option forwardfor` (X-Forwarded-For)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""

    binds: list[FrontendBindResponse] = []
    """Bind directives."""

    options: list[FrontendOptionResponse] = []
    """Frontend option directives."""


class FrontendListResponse(BaseModel):
    """Paginated list of frontends."""

    count: int
    """Total number of items."""

    items: list[FrontendDetailResponse]
    """List of result items."""


class AclRuleCreate(BaseModel):
    """Payload for creating a new ACL rule."""

    frontend_id: int | None = None
    """Foreign key to the parent frontend."""

    domain: str = Field(..., min_length=1, max_length=500)
    """Domain pattern for ACL matching."""

    backend_name: str | None = ""
    """Target backend name for matched requests."""

    acl_match_type: str = "hdr"
    """ACL match function (`hdr`, `hdr_dom`, etc.)."""

    is_redirect: bool = False
    """Whether this rule is a redirect instead of backend routing."""

    redirect_target: str | None = None
    """URL prefix for redirect rules."""

    redirect_code: int | None = 301
    """HTTP redirect status code (301, 302, etc.)."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int = 0
    """Display ordering index."""

    enabled: bool = True
    """Whether the rule is active."""


class AclRuleUpdate(BaseModel):
    """Payload for updating an existing ACL rule."""

    frontend_id: int | None = None
    """Foreign key to the parent frontend."""

    domain: str | None = None
    """Domain pattern for ACL matching."""

    backend_name: str | None = None
    """Target backend name for matched requests."""

    acl_match_type: str | None = None
    """ACL match function (`hdr`, `hdr_dom`, etc.)."""

    is_redirect: bool | None = None
    """Whether this rule is a redirect instead of backend routing."""

    redirect_target: str | None = None
    """URL prefix for redirect rules."""

    redirect_code: int | None = None
    """HTTP redirect status code (301, 302, etc.)."""

    comment: str | None = None
    """Optional user comment."""

    sort_order: int | None = None
    """Display ordering index."""

    enabled: bool | None = None
    """Whether the rule is active."""


class AclRuleResponse(BaseModel):
    """A single ACL rule returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    frontend_id: int | None
    """Foreign key to the parent frontend."""

    domain: str
    """Domain pattern for ACL matching."""

    backend_name: str | None
    """Target backend name for matched requests."""

    acl_match_type: str
    """ACL match function (`hdr`, `hdr_dom`, etc.)."""

    is_redirect: bool
    """Whether this rule is a redirect instead of backend routing."""

    redirect_target: str | None
    """URL prefix for redirect rules."""

    redirect_code: int | None
    """HTTP redirect status code (301, 302, etc.)."""

    comment: str | None
    """Optional user comment."""

    sort_order: int
    """Display ordering index."""

    enabled: bool
    """Whether the rule is active."""


class AclRuleListResponse(BaseModel):
    """Paginated list of ACL rules."""

    count: int
    """Total number of items."""

    items: list[AclRuleResponse]
    """List of result items."""
