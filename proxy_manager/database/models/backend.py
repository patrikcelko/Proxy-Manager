"""
Backend models
==============
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class Backend(Base):
    """HAProxy backend definition."""

    __tablename__ = "backends"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    mode: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Proxy mode (`http` or `tcp`)."""

    balance: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    option_forwardfor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option forwardfor` (X-Forwarded-For)."""

    option_redispatch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option redispatch` on connection failure."""

    retries: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Number of connection retries."""

    retry_on: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Conditions that trigger a retry (e.g. `conn-failure`)."""

    auth_userlist: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Userlist name for HTTP Basic authentication."""

    health_check_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable active health checking."""

    health_check_method: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """HTTP method for health checks."""

    health_check_uri: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """URI path for health checks."""

    errorfile: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Custom error file directive (e.g. `503 /errors/503.http`)."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    # Tier-1 additions
    cookie: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """Cookie-based persistence configuration."""

    timeout_server: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Server-side timeout."""

    timeout_connect: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Connection timeout."""

    timeout_queue: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Queue timeout."""

    http_check_expect: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """Expected response for HTTP health checks."""

    default_server_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Default server parameters applied to all servers."""

    http_reuse: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Connection reuse strategy."""

    hash_type: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Hash type for consistent hashing."""

    option_httplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option tcplog` (detailed TCP logging)."""

    compression_algo: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """MIME types to compress."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<Backend(id={self.id}, name={self.name!r})>"


class BackendServer(Base):
    """A server entry within a backend."""

    __tablename__ = "backend_servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    backend_id: Mapped[int] = mapped_column(ForeignKey("backends.id", ondelete="CASCADE"), nullable=False, index=True)
    """Foreign key to the parent backend."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Unique name identifier."""

    address: Mapped[str] = mapped_column(String(255), nullable=False)
    """Server IP address or hostname."""

    port: Mapped[int] = mapped_column(Integer, nullable=False)
    """Server port number."""

    check_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable health checks for this server."""

    maxconn: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maximum number of concurrent connections."""

    maxqueue: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maxqueue."""

    extra_params: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional server parameters (free-form text)."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    # Tier-1/2 additions
    weight: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Server weight for load balancing."""

    ssl_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable SSL/TLS for backend connections."""

    ssl_verify: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """SSL verification mode (`none`, `required`)."""

    backup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Mark as backup server (used only when primaries are down)."""

    inter: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Health check interval."""

    fastinter: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Health check interval when transitioning."""

    downinter: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Health check interval when server is down."""

    rise: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Consecutive successful checks before marking UP."""

    fall: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Consecutive failed checks before marking DOWN."""

    cookie_value: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Cookie value for server affinity."""

    send_proxy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable PROXY protocol v1."""

    send_proxy_v2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable PROXY protocol v2."""

    slowstart: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Slow-start ramp-up period after recovery."""

    resolve_prefer: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    """Preferred address family for DNS resolution."""

    resolvers_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Reference to a resolvers section for DNS."""

    on_marked_down: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Action when server is marked down."""

    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Whether the server is administratively disabled."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<BackendServer(id={self.id}, name={self.name!r}, address={self.address}:{self.port})>"


async def list_backends(session: AsyncSession) -> list[Backend]:
    """Return all backends ordered by name."""

    stmt = select(Backend).order_by(Backend.name)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_backend(session: AsyncSession, backend_id: int) -> Backend | None:
    """Fetch a single backend by primary key."""

    return await session.get(Backend, backend_id)


async def get_backend_by_name(session: AsyncSession, name: str) -> Backend | None:
    """Fetch a single backend by its unique name."""

    stmt = select(Backend).where(Backend.name == name)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def create_backend(
    session: AsyncSession,
    *,
    name: str,
    mode: str | None = None,
    balance: str | None = None,
    option_forwardfor: bool = False,
    option_redispatch: bool = False,
    retries: int | None = None,
    retry_on: str | None = None,
    auth_userlist: str | None = None,
    health_check_enabled: bool = False,
    health_check_method: str | None = None,
    health_check_uri: str | None = None,
    errorfile: str | None = None,
    comment: str | None = None,
    extra_options: str | None = None,
    cookie: str | None = None,
    timeout_server: str | None = None,
    timeout_connect: str | None = None,
    timeout_queue: str | None = None,
    http_check_expect: str | None = None,
    default_server_options: str | None = None,
    http_reuse: str | None = None,
    hash_type: str | None = None,
    option_httplog: bool = False,
    option_tcplog: bool = False,
    compression_algo: str | None = None,
    compression_type: str | None = None,
) -> Backend:
    """Create and persist a new backend."""

    be = Backend(
        name=name,
        mode=mode,
        balance=balance,
        option_forwardfor=option_forwardfor,
        option_redispatch=option_redispatch,
        retries=retries,
        retry_on=retry_on,
        auth_userlist=auth_userlist,
        health_check_enabled=health_check_enabled,
        health_check_method=health_check_method,
        health_check_uri=health_check_uri,
        errorfile=errorfile,
        comment=comment,
        extra_options=extra_options,
        cookie=cookie,
        timeout_server=timeout_server,
        timeout_connect=timeout_connect,
        timeout_queue=timeout_queue,
        http_check_expect=http_check_expect,
        default_server_options=default_server_options,
        http_reuse=http_reuse,
        hash_type=hash_type,
        option_httplog=option_httplog,
        option_tcplog=option_tcplog,
        compression_algo=compression_algo,
        compression_type=compression_type,
    )
    session.add(be)

    await session.commit()
    await session.refresh(be)

    return be


async def update_backend(
    session: AsyncSession,
    be: Backend,
    **kwargs: object,
) -> Backend:
    """Update an existing backend with the given field values."""

    allowed = {c.name for c in Backend.__table__.columns} - {"id"}
    for key, val in kwargs.items():
        if key in allowed:
            setattr(be, key, val)

    await session.commit()
    await session.refresh(be)

    return be


async def delete_backend(session: AsyncSession, be: Backend) -> None:
    """Delete a backend from the database."""

    await session.delete(be)
    await session.commit()


async def list_backend_servers(session: AsyncSession, backend_id: int) -> list[BackendServer]:
    """Return all servers for a given backend, ordered by sort_order."""

    stmt = (
        select(BackendServer)
        .where(BackendServer.backend_id == backend_id)
        .order_by(BackendServer.sort_order, BackendServer.id)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_backend_server(session: AsyncSession, server_id: int) -> BackendServer | None:
    """Fetch a single backend server by primary key."""

    return await session.get(BackendServer, server_id)


async def create_backend_server(
    session: AsyncSession,
    *,
    backend_id: int,
    name: str,
    address: str,
    port: int,
    check_enabled: bool = False,
    maxconn: int | None = None,
    maxqueue: int | None = None,
    extra_params: str | None = None,
    sort_order: int = 0,
    weight: int | None = None,
    ssl_enabled: bool = False,
    ssl_verify: str | None = None,
    backup: bool = False,
    inter: str | None = None,
    fastinter: str | None = None,
    downinter: str | None = None,
    rise: int | None = None,
    fall: int | None = None,
    cookie_value: str | None = None,
    send_proxy: bool = False,
    send_proxy_v2: bool = False,
    slowstart: str | None = None,
    resolve_prefer: str | None = None,
    resolvers_ref: str | None = None,
    on_marked_down: str | None = None,
    disabled: bool = False,
) -> BackendServer:
    """Create and persist a new backend server."""

    srv = BackendServer(
        backend_id=backend_id,
        name=name,
        address=address,
        port=port,
        check_enabled=check_enabled,
        maxconn=maxconn,
        maxqueue=maxqueue,
        extra_params=extra_params,
        sort_order=sort_order,
        weight=weight,
        ssl_enabled=ssl_enabled,
        ssl_verify=ssl_verify,
        backup=backup,
        inter=inter,
        fastinter=fastinter,
        downinter=downinter,
        rise=rise,
        fall=fall,
        cookie_value=cookie_value,
        send_proxy=send_proxy,
        send_proxy_v2=send_proxy_v2,
        slowstart=slowstart,
        resolve_prefer=resolve_prefer,
        resolvers_ref=resolvers_ref,
        on_marked_down=on_marked_down,
        disabled=disabled,
    )
    session.add(srv)

    await session.commit()
    await session.refresh(srv)

    return srv


async def update_backend_server(
    session: AsyncSession,
    srv: BackendServer,
    **kwargs: object,
) -> BackendServer:
    """Update an existing backend server with the given field values."""

    allowed = {c.name for c in BackendServer.__table__.columns} - {"id", "backend_id"}
    for key, val in kwargs.items():
        if key in allowed:
            setattr(srv, key, val)

    await session.commit()
    await session.refresh(srv)
    return srv


async def delete_backend_server(session: AsyncSession, srv: BackendServer) -> None:
    """Delete a backend server from the database."""

    await session.delete(srv)
    await session.commit()


async def delete_all_backends(session: AsyncSession) -> None:
    """Delete all backends and their servers."""

    for model in (BackendServer, Backend):
        await session.execute(delete(model))

    await session.commit()
