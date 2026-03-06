"""
Listen block model
==================
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class ListenBlock(Base):
    """HAProxy 'listen' section (e.g. stats)."""

    __tablename__ = "listen_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="http")
    """Proxy mode (`http` or `tcp`)."""

    balance: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Load-balancing algorithm (e.g. `roundrobin`)."""

    maxconn: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maximum number of concurrent connections."""

    timeout_client: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Client-side timeout."""

    timeout_server: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Server-side timeout."""

    timeout_connect: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    """Connection timeout."""

    default_server_params: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Default server parameters applied to all servers."""

    option_httplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option httplog` (detailed HTTP logging)."""

    option_tcplog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option tcplog` (detailed TCP logging)."""

    option_forwardfor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Enable `option forwardfor` (X-Forwarded-For)."""

    content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Raw configuration content."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<ListenBlock(id={self.id}, name={self.name!r})>"


class ListenBlockBind(Base):
    """A bind directive for a listen block."""

    __tablename__ = "listen_block_binds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    listen_block_id: Mapped[int] = mapped_column(
        ForeignKey("listen_blocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    """Foreign key to the parent listen block."""

    bind_line: Mapped[str] = mapped_column(Text, nullable=False)
    """Full bind directive (address, port, options)."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<ListenBlockBind(id={self.id}, bind_line={self.bind_line!r})>"


async def list_listen_blocks(session: AsyncSession) -> list[ListenBlock]:
    """Return all listen blocks ordered by sort_order."""

    stmt = select(ListenBlock).order_by(ListenBlock.sort_order, ListenBlock.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_listen_block(session: AsyncSession, block_id: int) -> ListenBlock | None:
    """Fetch a single listen block by primary key."""

    return await session.get(ListenBlock, block_id)


async def get_listen_block_by_name(session: AsyncSession, name: str) -> ListenBlock | None:
    """Fetch a single listen block by its unique name."""

    stmt = select(ListenBlock).where(ListenBlock.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_listen_block(
    session: AsyncSession,
    *,
    name: str,
    mode: str = "http",
    balance: str | None = None,
    maxconn: int | None = None,
    timeout_client: str | None = None,
    timeout_server: str | None = None,
    timeout_connect: str | None = None,
    default_server_params: str | None = None,
    option_httplog: bool = False,
    option_tcplog: bool = False,
    option_forwardfor: bool = False,
    content: str | None = None,
    comment: str | None = None,
    sort_order: int = 0,
) -> ListenBlock:
    """Create and persist a new listen block."""

    block = ListenBlock(
        name=name,
        mode=mode,
        balance=balance,
        maxconn=maxconn,
        timeout_client=timeout_client,
        timeout_server=timeout_server,
        timeout_connect=timeout_connect,
        default_server_params=default_server_params,
        option_httplog=option_httplog,
        option_tcplog=option_tcplog,
        option_forwardfor=option_forwardfor,
        content=content,
        comment=comment,
        sort_order=sort_order,
    )
    session.add(block)
    await session.commit()
    await session.refresh(block)
    return block


async def update_listen_block(
    session: AsyncSession,
    block: ListenBlock,
    **kwargs: object,
) -> ListenBlock:
    """Update an existing listen block with the given field values."""

    allowed = {c.name for c in ListenBlock.__table__.columns} - {"id"}
    for key, val in kwargs.items():
        if key in allowed:
            setattr(block, key, val)
    await session.commit()
    await session.refresh(block)
    return block


async def delete_listen_block(session: AsyncSession, block: ListenBlock) -> None:
    """Delete a listen block from the database."""

    await session.delete(block)
    await session.commit()


async def delete_all_listen_blocks(session: AsyncSession) -> None:
    """Delete all listen blocks and their binds."""

    await session.execute(delete(ListenBlockBind))
    await session.execute(delete(ListenBlock))
    await session.commit()


async def list_listen_block_binds(session: AsyncSession, listen_block_id: int) -> list[ListenBlockBind]:
    """Return all binds for a given listen block."""

    stmt = (
        select(ListenBlockBind)
        .where(ListenBlockBind.listen_block_id == listen_block_id)
        .order_by(ListenBlockBind.sort_order, ListenBlockBind.id)
    )
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_listen_block_bind(session: AsyncSession, bind_id: int) -> ListenBlockBind | None:
    """Fetch a single listen block bind by primary key."""

    return await session.get(ListenBlockBind, bind_id)


async def create_listen_block_bind(
    session: AsyncSession,
    *,
    listen_block_id: int,
    bind_line: str,
    sort_order: int = 0,
) -> ListenBlockBind:
    """Create and persist a new listen block bind."""

    bind = ListenBlockBind(
        listen_block_id=listen_block_id,
        bind_line=bind_line,
        sort_order=sort_order,
    )
    session.add(bind)

    await session.commit()
    await session.refresh(bind)

    return bind


async def update_listen_block_bind(
    session: AsyncSession,
    bind: ListenBlockBind,
    *,
    bind_line: str | None = None,
    sort_order: int | None = None,
) -> ListenBlockBind:
    """Update an existing listen block bind."""

    if bind_line is not None:
        bind.bind_line = bind_line
    if sort_order is not None:
        bind.sort_order = sort_order

    await session.commit()
    await session.refresh(bind)

    return bind


async def delete_listen_block_bind(session: AsyncSession, bind: ListenBlockBind) -> None:
    """Delete a listen block bind from the database."""

    await session.delete(bind)
    await session.commit()
