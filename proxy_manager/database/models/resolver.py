"""
Resolver model
==============
"""

from sqlalchemy import ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class Resolver(Base):
    """HAProxy 'resolvers' section."""

    __tablename__ = "resolvers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique name identifier."""

    resolve_retries: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Number of DNS resolution retries."""

    timeout_resolve: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """DNS resolution timeout."""

    timeout_retry: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """DNS retry timeout."""

    hold_valid: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for valid DNS responses."""

    hold_other: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for other DNS response codes."""

    hold_refused: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for refused DNS responses."""

    hold_timeout: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for DNS timeouts."""

    hold_obsolete: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for obsolete DNS entries."""

    hold_nx: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for NXDOMAIN responses."""

    hold_aa: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    """Hold time for authoritative answers."""

    accepted_payload_size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Maximum accepted DNS payload size in bytes."""

    parse_resolv_conf: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # 0 or 1
    """Parse `/etc/resolv.conf` (1 = enabled)."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    extra_options: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Additional HAProxy directives (free-form text)."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<Resolver(id={self.id}, name={self.name!r})>"


class ResolverNameserver(Base):
    """A nameserver entry within a resolver."""

    __tablename__ = "resolver_nameservers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    resolver_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resolvers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """Foreign key to the parent resolver."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Unique name identifier."""

    address: Mapped[str] = mapped_column(String(255), nullable=False)
    """Server IP address or hostname."""

    port: Mapped[int] = mapped_column(Integer, nullable=False, default=53)
    """Server port number."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<ResolverNameserver(id={self.id}, name={self.name!r})>"


async def list_resolvers(session: AsyncSession) -> list[Resolver]:
    """Return all resolvers ordered by name."""

    result = await session.execute(select(Resolver).order_by(Resolver.name))
    return list(result.scalars().all())


async def get_resolver(session: AsyncSession, resolver_id: int) -> Resolver | None:
    """Fetch a single resolver by primary key."""

    return await session.get(Resolver, resolver_id)


async def get_resolver_by_name(session: AsyncSession, name: str) -> Resolver | None:
    """Fetch a single resolver by its unique name."""

    result = await session.execute(select(Resolver).where(Resolver.name == name))
    return result.scalar_one_or_none()


async def create_resolver(session: AsyncSession, **kwargs: object) -> Resolver:
    """Create and persist a new resolver."""

    obj = Resolver(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_resolver(session: AsyncSession, obj: Resolver, **kwargs: object) -> Resolver:
    """Update an existing resolver with the given field values."""

    allowed = {c.name for c in Resolver.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_resolver(session: AsyncSession, obj: Resolver) -> None:
    """Delete a resolver from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_resolvers(session: AsyncSession) -> None:
    """Delete all resolvers and their nameservers."""

    await session.execute(delete(ResolverNameserver))
    await session.execute(delete(Resolver))
    await session.commit()


async def get_resolver_nameserver(session: AsyncSession, ns_id: int) -> ResolverNameserver | None:
    """Fetch a single resolver nameserver by primary key."""

    return await session.get(ResolverNameserver, ns_id)


async def list_resolver_nameservers(session: AsyncSession, resolver_id: int) -> list[ResolverNameserver]:
    """Return all nameservers for a given resolver."""

    result = await session.execute(
        select(ResolverNameserver)
        .where(ResolverNameserver.resolver_id == resolver_id)
        .order_by(ResolverNameserver.sort_order, ResolverNameserver.id)
    )

    return list(result.scalars().all())


async def create_resolver_nameserver(session: AsyncSession, **kwargs: object) -> ResolverNameserver:
    """Create and persist a new resolver nameserver."""

    obj = ResolverNameserver(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_resolver_nameserver(
    session: AsyncSession,
    obj: ResolverNameserver,
    **kwargs: object,
) -> ResolverNameserver:
    """Update an existing resolver nameserver."""

    allowed = {c.name for c in ResolverNameserver.__table__.columns} - {"id"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_resolver_nameserver(session: AsyncSession, obj: ResolverNameserver) -> None:
    """Delete a resolver nameserver from the database."""

    await session.delete(obj)
    await session.commit()
