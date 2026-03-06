"""
SSL Certificate model
=====================
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class SslCertificate(Base):
    """An SSL/TLS certificate record."""

    __tablename__ = "ssl_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """Primary key."""

    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    """Domain pattern for ACL matching."""

    alt_domains: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Subject Alternative Names (comma-separated)."""

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Unique email address."""

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="certbot",
    )  # certbot | manual | self-signed
    """Certificate provider (`certbot`, `manual`, `self-signed`)."""

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )  # pending | active | expired | revoked | error
    """Certificate status (`pending`, `active`, `expired`, etc.)."""

    cert_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Path to the certificate file."""

    key_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Path to the private key file."""

    fullchain_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    """Path to the full certificate chain."""

    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    """Certificate issuance timestamp."""

    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    """Certificate expiry timestamp."""

    auto_renew: Mapped[bool] = mapped_column(default=True)
    """Enable automatic renewal."""

    challenge_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="http-01",
    )  # http-01 | dns-01 | standalone
    """ACME challenge type (`http-01`, `dns-01`)."""

    dns_plugin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    """DNS plugin for ACME challenge."""

    last_renewal_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    """Last renewal timestamp."""

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Last error message."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Optional user comment."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    """Record creation timestamp."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    """Last update timestamp."""


async def list_ssl_certificates(session: AsyncSession) -> list[SslCertificate]:
    """Return all SSL certificates ordered by domain."""

    result = await session.execute(
        select(SslCertificate).order_by(SslCertificate.domain),
    )
    return list(result.scalars().all())


async def get_ssl_certificate(session: AsyncSession, cert_id: int) -> SslCertificate | None:
    """Fetch a single SSL certificate by primary key."""

    return await session.get(SslCertificate, cert_id)


async def get_ssl_certificate_by_domain(session: AsyncSession, domain: str) -> SslCertificate | None:
    """Fetch a single SSL certificate by domain."""

    result = await session.execute(
        select(SslCertificate).where(SslCertificate.domain == domain),
    )
    return result.scalar_one_or_none()


async def create_ssl_certificate(session: AsyncSession, **kwargs: object) -> SslCertificate:
    """Create and persist a new SSL certificate record."""

    obj = SslCertificate(**kwargs)
    session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return obj


async def update_ssl_certificate(
    session: AsyncSession,
    obj: SslCertificate,
    **kwargs: object,
) -> SslCertificate:
    """Update an existing SSL certificate record."""

    allowed = {c.name for c in SslCertificate.__table__.columns} - {"id", "created_at"}
    for k, v in kwargs.items():
        if k in allowed:
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)

    return obj


async def delete_ssl_certificate(session: AsyncSession, obj: SslCertificate) -> None:
    """Delete an SSL certificate record from the database."""

    await session.delete(obj)
    await session.commit()


async def delete_all_ssl_certificates(session: AsyncSession) -> None:
    """Delete all SSL certificate records."""

    await session.execute(delete(SslCertificate))
    await session.commit()
