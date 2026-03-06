"""
Frontend model
==============
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class Frontend(Base):
    """HAProxy frontend definition."""

    __tablename__ = "frontends"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    default_backend: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Default backend when no ACL matches."""

    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="http")
    """Proxy mode (`http` or `tcp`)."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    # Tier-1 additions
    timeout_client: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Client-side timeout."""

    timeout_http_request: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Timeout for receiving the HTTP request."""

    timeout_http_keep_alive: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Timeout for HTTP keep-alive connections."""

    maxconn: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maximum number of concurrent connections."""

    option_httplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option forwardfor` (X-Forwarded-For)."""

    compression_algo: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Compression algorithm (e.g. `gzip`)."""

    compression_type: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    """MIME types to compress."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<Frontend(id={self.id}, name={self.name!r})>"


class FrontendBind(Base):
    """A bind directive for a frontend."""

    __tablename__ = "frontend_binds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    frontend_id: Mapped[int] = mapped_column(ForeignKey("frontends.id", ondelete="CASCADE"), nullable=False, index=True)
    """Foreign key to the parent frontend."""

    bind_line: Mapped[str] = mapped_column(Text, nullable=False)
    """Full bind directive (address, port, options)."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<FrontendBind(id={self.id}, bind_line={self.bind_line!r})>"


class FrontendOption(Base):
    """An option/directive within a frontend (headers, DDoS rules, etc.)."""

    __tablename__ = "frontend_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    frontend_id: Mapped[int] = mapped_column(ForeignKey("frontends.id", ondelete="CASCADE"), nullable=False, index=True)
    """Foreign key to the parent frontend."""

    directive: Mapped[str] = mapped_column(Text, nullable=False)
    """HAProxy directive name."""

    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    """Directive value."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<FrontendOption(id={self.id}, directive={self.directive!r})>"


async def list_frontends(session: AsyncSession) -> list[Frontend]:
    """Return all frontends ordered by name."""

    stmt = select(Frontend).order_by(Frontend.name)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_frontend(session: AsyncSession, frontend_id: int) -> Frontend | None:
    """Fetch a single frontend by primary key."""

    return await session.get(Frontend, frontend_id)


async def get_frontend_by_name(session: AsyncSession, name: str) -> Frontend | None:
    """Fetch a single frontend by its unique name."""

    stmt = select(Frontend).where(Frontend.name == name)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def create_frontend(
    session: AsyncSession,
    *,
    name: str,
    default_backend: str | None = None,
    mode: str = "http",
    comment: str | None = None,
    timeout_client: str | None = None,
    timeout_http_request: str | None = None,
    timeout_http_keep_alive: str | None = None,
    maxconn: int | None = None,
    option_httplog: bool = False,
    option_tcplog: bool = False,
    option_forwardfor: bool = False,
    compression_algo: str | None = None,
    compression_type: str | None = None,
) -> Frontend:
    """Create and persist a new frontend."""

    fe = Frontend(
        name=name,
        default_backend=default_backend,
        mode=mode,
        comment=comment,
        timeout_client=timeout_client,
        timeout_http_request=timeout_http_request,
        timeout_http_keep_alive=timeout_http_keep_alive,
        maxconn=maxconn,
        option_httplog=option_httplog,
        option_tcplog=option_tcplog,
        option_forwardfor=option_forwardfor,
        compression_algo=compression_algo,
        compression_type=compression_type,
    )
    session.add(fe)

    await session.commit()
    await session.refresh(fe)

    return fe


async def update_frontend(
    session: AsyncSession,
    fe: Frontend,
    *,
    name: str | None = None,
    default_backend: str | None = None,
    mode: str | None = None,
    comment: str | None = None,
    timeout_client: str | None = None,
    timeout_http_request: str | None = None,
    timeout_http_keep_alive: str | None = None,
    maxconn: int | None = None,
    option_httplog: bool | None = None,
    option_tcplog: bool | None = None,
    option_forwardfor: bool | None = None,
    compression_algo: str | None = None,
    compression_type: str | None = None,
    fields_set: frozenset[str] | None = None,
) -> Frontend:
    """Update an existing frontend with the given field values."""

    direct_fields = {
        "name": name,
        "mode": mode,
        "option_httplog": option_httplog,
        "option_tcplog": option_tcplog,
        "option_forwardfor": option_forwardfor,
        "timeout_client": timeout_client,
        "timeout_http_request": timeout_http_request,
        "timeout_http_keep_alive": timeout_http_keep_alive,
        "maxconn": maxconn,
        "compression_algo": compression_algo,
        "compression_type": compression_type,
        "default_backend": default_backend,
        "comment": comment,
    }

    for field_name, value in direct_fields.items():
        if fields_set and field_name in fields_set:
            # Explicit field set from API (allows setting nullable fields to None)
            setattr(fe, field_name, value)
        elif value is not None:
            setattr(fe, field_name, value)

    await session.commit()
    await session.refresh(fe)

    return fe


async def delete_frontend(session: AsyncSession, fe: Frontend) -> None:
    """Delete a frontend from the database."""

    await session.delete(fe)
    await session.commit()


async def list_frontend_binds(session: AsyncSession, frontend_id: int) -> list[FrontendBind]:
    """Return all binds for a given frontend."""

    stmt = (
        select(FrontendBind)
        .where(FrontendBind.frontend_id == frontend_id)
        .order_by(FrontendBind.sort_order, FrontendBind.id)
    )
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def create_frontend_bind(
    session: AsyncSession, *, frontend_id: int, bind_line: str, sort_order: int = 0
) -> FrontendBind:
    """Create and persist a new frontend bind."""

    bind = FrontendBind(frontend_id=frontend_id, bind_line=bind_line, sort_order=sort_order)
    session.add(bind)

    await session.commit()
    await session.refresh(bind)

    return bind


async def delete_frontend_bind(session: AsyncSession, bind: FrontendBind) -> None:
    """Delete a frontend bind from the database."""

    await session.delete(bind)
    await session.commit()


async def update_frontend_bind(
    session: AsyncSession,
    bind: FrontendBind,
    *,
    bind_line: str | None = None,
    sort_order: int | None = None,
) -> FrontendBind:
    """Update an existing frontend bind."""

    if bind_line is not None:
        bind.bind_line = bind_line

    if sort_order is not None:
        bind.sort_order = sort_order

    await session.commit()
    await session.refresh(bind)

    return bind


async def get_frontend_bind(session: AsyncSession, bind_id: int) -> FrontendBind | None:
    """Fetch a single frontend bind by primary key."""

    return await session.get(FrontendBind, bind_id)


async def list_frontend_options(session: AsyncSession, frontend_id: int) -> list[FrontendOption]:
    """Return all options for a given frontend."""

    stmt = (
        select(FrontendOption)
        .where(FrontendOption.frontend_id == frontend_id)
        .order_by(FrontendOption.sort_order, FrontendOption.id)
    )
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def create_frontend_option(
    session: AsyncSession,
    *,
    frontend_id: int,
    directive: str,
    value: str = "",
    comment: str | None = None,
    sort_order: int = 0,
) -> FrontendOption:
    """Create and persist a new frontend option."""

    opt = FrontendOption(
        frontend_id=frontend_id,
        directive=directive,
        value=value,
        comment=comment,
        sort_order=sort_order,
    )
    session.add(opt)

    await session.commit()
    await session.refresh(opt)

    return opt


async def delete_frontend_option(session: AsyncSession, opt: FrontendOption) -> None:
    """Delete a frontend option from the database."""

    await session.delete(opt)
    await session.commit()


async def update_frontend_option(
    session: AsyncSession,
    opt: FrontendOption,
    *,
    directive: str | None = None,
    value: str | None = None,
    comment: str | None = None,
    sort_order: int | None = None,
) -> FrontendOption:
    """Update an existing frontend option."""

    if directive is not None:
        opt.directive = directive

    if value is not None:
        opt.value = value

    if comment is not None:
        opt.comment = comment

    if sort_order is not None:
        opt.sort_order = sort_order

    await session.commit()
    await session.refresh(opt)

    return opt


async def get_frontend_option(session: AsyncSession, option_id: int) -> FrontendOption | None:
    """Fetch a single frontend option by primary key."""

    return await session.get(FrontendOption, option_id)


async def delete_all_frontends(session: AsyncSession) -> None:
    """Delete all frontends, binds, and options."""

    for model in (FrontendOption, FrontendBind, Frontend):
        await session.execute(delete(model))

    await session.commit()
