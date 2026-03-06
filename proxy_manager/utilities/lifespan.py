"""
Application lifespan management
===============================
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from sqlalchemy import select

from proxy_manager.database import Base, engine
from proxy_manager.database.connection import async_session_factory
from proxy_manager.database.models.ssl_certificate import SslCertificate

logger = logging.getLogger(__name__)

# Check every 6 hours
CERT_CHECK_INTERVAL = 6 * 60 * 60

# Warn when cert expires within 30 days
CERT_EXPIRY_WARNING_DAYS = 30


async def _check_ssl_certificates():
    """Background task that periodically checks SSL certificate expiry
    and updates statuses accordingly.
    """

    while True:
        try:
            await asyncio.sleep(CERT_CHECK_INTERVAL)
            async with async_session_factory() as session:
                now = datetime.now(UTC)
                warn_threshold = now + timedelta(days=CERT_EXPIRY_WARNING_DAYS)

                # Mark expired certificates
                result = await session.execute(
                    select(SslCertificate).where(
                        SslCertificate.status == "active",
                        SslCertificate.expires_at.isnot(None),
                        SslCertificate.expires_at < now,
                    )
                )
                expired_certs = result.scalars().all()
                for cert in expired_certs:
                    if cert.expires_at is None:
                        continue

                    cert.status = "expired"
                    cert.last_error = f"Certificate expired on {cert.expires_at.strftime('%Y-%m-%d')}"
                    logger.warning(
                        "SSL certificate for %s has expired (was %s)",
                        cert.domain,
                        cert.expires_at,
                    )

                # Log warnings for soon-to-expire certificates
                result = await session.execute(
                    select(SslCertificate).where(
                        SslCertificate.status == "active",
                        SslCertificate.expires_at.isnot(None),
                        SslCertificate.expires_at >= now,
                        SslCertificate.expires_at <= warn_threshold,
                    )
                )
                expiring_certs = result.scalars().all()
                for cert in expiring_certs:
                    if cert.expires_at is None:
                        continue

                    days_left = (
                        (cert.expires_at.replace(tzinfo=UTC) - now).days
                        if cert.expires_at.tzinfo is None
                        else (cert.expires_at - now).days
                    )
                    logger.warning(
                        "SSL certificate for %s expires in %d days (auto_renew=%s)",
                        cert.domain,
                        days_left,
                        cert.auto_renew,
                    )

                await session.commit()
                logger.info(
                    "SSL certificate check complete: %d expired, %d expiring soon",
                    len(expired_certs),
                    len(expiring_certs),
                )
        except asyncio.CancelledError:
            logger.info("SSL certificate check task cancelled")
            break
        except Exception:
            logger.exception("Error during SSL certificate check")
            await asyncio.sleep(60)  # Retry after 1 minute on error


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup, start background tasks."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background SSL certificate checker
    cert_task = asyncio.create_task(_check_ssl_certificates())
    logger.info("Started background SSL certificate expiry checker (interval: %dh)", CERT_CHECK_INTERVAL // 3600)

    yield

    # Cleanup
    cert_task.cancel()
    try:
        await cert_task
    except asyncio.CancelledError:
        logger.info("Background SSL certificate checker task cancelled successfully.")
