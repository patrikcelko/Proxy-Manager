"""
Backend schemas
===============

Request/response schemas for backends and their server entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class BackendCreate(BaseModel):
    """Payload for creating a new backend."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    mode: str | None = None
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None = None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    option_forwardfor: bool = False
    """Enable `option forwardfor` (X-Forwarded-For)."""

    option_redispatch: bool = False
    """Enable `option redispatch` on connection failure."""

    retries: int | None = None
    """Number of connection retries."""

    retry_on: str | None = None
    """Conditions that trigger a retry (e.g. `conn-failure`)."""

    auth_userlist: str | None = None
    """Userlist name for HTTP Basic authentication."""

    health_check_enabled: bool = False
    """Enable active health checking."""

    health_check_method: str | None = None
    """HTTP method for health checks."""

    health_check_uri: str | None = None
    """URI path for health checks."""

    errorfile: str | None = None
    """Custom error file directive (e.g. `503 /errors/503.http`)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    cookie: str | None = None
    """Cookie-based persistence configuration."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    timeout_queue: str | None = None
    """Queue timeout."""

    http_check_expect: str | None = None
    """Expected response for HTTP health checks."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""

    http_reuse: str | None = None
    """Connection reuse strategy."""

    hash_type: str | None = None
    """Hash type for consistent hashing."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""


class BackendUpdate(BaseModel):
    """Payload for updating an existing backend."""

    name: str | None = None
    """Unique name identifier."""

    mode: str | None = None
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None = None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    option_forwardfor: bool | None = None
    """Enable `option forwardfor` (X-Forwarded-For)."""

    option_redispatch: bool | None = None
    """Enable `option redispatch` on connection failure."""

    retries: int | None = None
    """Number of connection retries."""

    retry_on: str | None = None
    """Conditions that trigger a retry (e.g. `conn-failure`)."""

    auth_userlist: str | None = None
    """Userlist name for HTTP Basic authentication."""

    health_check_enabled: bool | None = None
    """Enable active health checking."""

    health_check_method: str | None = None
    """HTTP method for health checks."""

    health_check_uri: str | None = None
    """URI path for health checks."""

    errorfile: str | None = None
    """Custom error file directive (e.g. `503 /errors/503.http`)."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    cookie: str | None = None
    """Cookie-based persistence configuration."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    timeout_queue: str | None = None
    """Queue timeout."""

    http_check_expect: str | None = None
    """Expected response for HTTP health checks."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""

    http_reuse: str | None = None
    """Connection reuse strategy."""

    hash_type: str | None = None
    """Hash type for consistent hashing."""

    option_httplog: bool | None = None
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool | None = None
    """Enable `option tcplog` (detailed TCP logging)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""


class BackendServerCreate(BaseModel):
    """Payload for creating a backend server."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    address: str = Field(..., min_length=1)
    """Server IP address or hostname."""

    port: int = Field(..., ge=1, le=65535)
    """Server port number."""

    check_enabled: bool = False
    """Enable health checks for this server."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    maxqueue: int | None = None
    """Maxqueue."""

    extra_params: str | None = None
    """Additional server parameters (free-form text)."""

    sort_order: int = 0
    """Display ordering index."""

    weight: int | None = None
    """Server weight for load balancing."""

    ssl_enabled: bool = False
    """Enable SSL/TLS for backend connections."""

    ssl_verify: str | None = None
    """SSL verification mode (`none`, `required`)."""

    backup: bool = False
    """Mark as backup server (used only when primaries are down)."""

    inter: str | None = None
    """Health check interval."""

    fastinter: str | None = None
    """Health check interval when transitioning."""

    downinter: str | None = None
    """Health check interval when server is down."""

    rise: int | None = None
    """Consecutive successful checks before marking UP."""

    fall: int | None = None
    """Consecutive failed checks before marking DOWN."""

    cookie_value: str | None = None
    """Cookie value for server affinity."""

    send_proxy: bool = False
    """Enable PROXY protocol v1."""

    send_proxy_v2: bool = False
    """Enable PROXY protocol v2."""

    slowstart: str | None = None
    """Slow-start ramp-up period after recovery."""

    resolve_prefer: str | None = None
    """Preferred address family for DNS resolution."""

    resolvers_ref: str | None = None
    """Reference to a resolvers section for DNS."""

    on_marked_down: str | None = None
    """Action when server is marked down."""

    disabled: bool = False
    """Whether the server is administratively disabled."""


class BackendServerUpdate(BaseModel):
    """Payload for updating a backend server."""

    name: str | None = None
    """Unique name identifier."""

    address: str | None = None
    """Server IP address or hostname."""

    port: int | None = None
    """Server port number."""

    check_enabled: bool | None = None
    """Enable health checks for this server."""

    maxconn: int | None = None
    """Maximum number of concurrent connections."""

    maxqueue: int | None = None
    """Maxqueue."""

    extra_params: str | None = None
    """Additional server parameters (free-form text)."""

    sort_order: int | None = None
    """Display ordering index."""

    weight: int | None = None
    """Server weight for load balancing."""

    ssl_enabled: bool | None = None
    """Enable SSL/TLS for backend connections."""

    ssl_verify: str | None = None
    """SSL verification mode (`none`, `required`)."""

    backup: bool | None = None
    """Mark as backup server (used only when primaries are down)."""

    inter: str | None = None
    """Health check interval."""

    fastinter: str | None = None
    """Health check interval when transitioning."""

    downinter: str | None = None
    """Health check interval when server is down."""

    rise: int | None = None
    """Consecutive successful checks before marking UP."""

    fall: int | None = None
    """Consecutive failed checks before marking DOWN."""

    cookie_value: str | None = None
    """Cookie value for server affinity."""

    send_proxy: bool | None = None
    """Enable PROXY protocol v1."""

    send_proxy_v2: bool | None = None
    """Enable PROXY protocol v2."""

    slowstart: str | None = None
    """Slow-start ramp-up period after recovery."""

    resolve_prefer: str | None = None
    """Preferred address family for DNS resolution."""

    resolvers_ref: str | None = None
    """Reference to a resolvers section for DNS."""

    on_marked_down: str | None = None
    """Action when server is marked down."""

    disabled: bool | None = None
    """Whether the server is administratively disabled."""


class BackendServerResponse(BaseModel):
    """A single backend server returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    backend_id: int
    """Foreign key to the parent backend."""

    name: str
    """Unique name identifier."""

    address: str
    """Server IP address or hostname."""

    port: int
    """Server port number."""

    check_enabled: bool
    """Enable health checks for this server."""

    maxconn: int | None
    """Maximum number of concurrent connections."""

    maxqueue: int | None
    """Maxqueue."""

    extra_params: str | None
    """Additional server parameters (free-form text)."""

    sort_order: int
    """Display ordering index."""

    weight: int | None = None
    """Server weight for load balancing."""

    ssl_enabled: bool = False
    """Enable SSL/TLS for backend connections."""

    ssl_verify: str | None = None
    """SSL verification mode (`none`, `required`)."""

    backup: bool = False
    """Mark as backup server (used only when primaries are down)."""

    inter: str | None = None
    """Health check interval."""

    fastinter: str | None = None
    """Health check interval when transitioning."""

    downinter: str | None = None
    """Health check interval when server is down."""

    rise: int | None = None
    """Consecutive successful checks before marking UP."""

    fall: int | None = None
    """Consecutive failed checks before marking DOWN."""

    cookie_value: str | None = None
    """Cookie value for server affinity."""

    send_proxy: bool = False
    """Enable PROXY protocol v1."""

    send_proxy_v2: bool = False
    """Enable PROXY protocol v2."""

    slowstart: str | None = None
    """Slow-start ramp-up period after recovery."""

    resolve_prefer: str | None = None
    """Preferred address family for DNS resolution."""

    resolvers_ref: str | None = None
    """Reference to a resolvers section for DNS."""

    on_marked_down: str | None = None
    """Action when server is marked down."""

    disabled: bool = False
    """Whether the server is administratively disabled."""


class BackendDetailResponse(BaseModel):
    """Backend with its server entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    mode: str | None
    """Proxy mode (`http` or `tcp`)."""

    balance: str | None
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    option_forwardfor: bool
    """Enable `option forwardfor` (X-Forwarded-For)."""

    option_redispatch: bool
    """Enable `option redispatch` on connection failure."""

    retries: int | None
    """Number of connection retries."""

    retry_on: str | None
    """Conditions that trigger a retry (e.g. `conn-failure`)."""

    auth_userlist: str | None
    """Userlist name for HTTP Basic authentication."""

    health_check_enabled: bool
    """Enable active health checking."""

    health_check_method: str | None
    """HTTP method for health checks."""

    health_check_uri: str | None
    """URI path for health checks."""

    errorfile: str | None
    """Custom error file directive (e.g. `503 /errors/503.http`)."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None
    """Additional HAProxy directives (free-form text)."""

    cookie: str | None = None
    """Cookie-based persistence configuration."""

    timeout_server: str | None = None
    """Server-side timeout."""

    timeout_connect: str | None = None
    """Connection timeout."""

    timeout_queue: str | None = None
    """Queue timeout."""

    http_check_expect: str | None = None
    """Expected response for HTTP health checks."""

    default_server_options: str | None = None
    """Default server parameters applied to all servers."""

    http_reuse: str | None = None
    """Connection reuse strategy."""

    hash_type: str | None = None
    """Hash type for consistent hashing."""

    option_httplog: bool = False
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: bool = False
    """Enable `option tcplog` (detailed TCP logging)."""

    compression_algo: str | None = None
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: str | None = None
    """MIME types to compress."""

    servers: list[BackendServerResponse] = []
    """Backend server entries."""


class BackendListResponse(BaseModel):
    """Paginated list of backends."""

    count: int
    """Total number of items."""

    items: list[BackendDetailResponse]
    """List of result items."""
