"""
Application lifespan management
===============================
"""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

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

# Config mount check interval (seconds)
MOUNT_CHECK_INTERVAL = 30


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

                    days_left = (cert.expires_at.replace(tzinfo=UTC) - now).days if cert.expires_at.tzinfo is None else (cert.expires_at - now).days
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

    # Start background config mount watcher
    mount_task = asyncio.create_task(_config_mount_watcher())
    logger.info("Started background config mount watcher (interval: %ds)", MOUNT_CHECK_INTERVAL)

    yield

    # Cleanup
    cert_task.cancel()
    mount_task.cancel()
    try:
        await cert_task
    except asyncio.CancelledError:
        logger.info("Background SSL certificate checker task cancelled successfully.")
    try:
        await mount_task
    except asyncio.CancelledError:
        logger.info("Background config mount watcher task cancelled successfully.")


async def _config_mount_watcher() -> None:
    """Background task that watches for new committed versions and
    regenerates the HAProxy config file in the mount directory.
    """

    last_hash: str | None = None
    mount_dir = Path(os.environ.get("PM_MOUNT_DIR", ".mount"))

    while True:
        try:
            await asyncio.sleep(MOUNT_CHECK_INTERVAL)

            async with async_session_factory() as session:
                from proxy_manager.database.models.config_version import get_latest_version

                latest = await get_latest_version(session)
                if latest is None or latest.hash == last_hash:
                    continue

                # New version detected — regenerate config
                from proxy_manager.config_parser.generator import generate_config
                from proxy_manager.database.models.backend import list_backend_servers, list_backends
                from proxy_manager.database.models.cache import list_cache_sections
                from proxy_manager.database.models.default_setting import list_default_settings
                from proxy_manager.database.models.frontend import list_frontend_binds, list_frontend_options, list_frontends
                from proxy_manager.database.models.global_setting import list_global_settings
                from proxy_manager.database.models.http_errors import list_http_error_entries, list_http_errors_sections
                from proxy_manager.database.models.listen_block import list_listen_block_binds, list_listen_blocks
                from proxy_manager.database.models.mailer import list_mailer_entries, list_mailer_sections
                from proxy_manager.database.models.peer import list_peer_entries, list_peer_sections
                from proxy_manager.database.models.resolver import list_resolver_nameservers, list_resolvers
                from proxy_manager.database.models.userlist import list_userlist_entries, list_userlists
                from proxy_manager.database.models.acl_rule import list_acl_rules

                gs = await list_global_settings(session)
                ds = await list_default_settings(session)

                lbs_raw = await list_listen_blocks(session)
                listen_blocks = []
                for lb in lbs_raw:
                    lb_binds = await list_listen_block_binds(session, lb.id)
                    listen_blocks.append((lb, lb_binds))

                uls_raw = await list_userlists(session)
                userlists = []
                for ul in uls_raw:
                    entries = await list_userlist_entries(session, ul.id)
                    userlists.append((ul, entries))

                fes_raw = await list_frontends(session)
                frontends = []
                for fe in fes_raw:
                    binds = await list_frontend_binds(session, fe.id)
                    opts = await list_frontend_options(session, fe.id)
                    acls = await list_acl_rules(session, fe.id)
                    frontends.append((fe, binds, opts, acls))

                bes_raw = await list_backends(session)
                backends = []
                for be in bes_raw:
                    srvs = await list_backend_servers(session, be.id)
                    backends.append((be, srvs))

                res_raw = await list_resolvers(session)
                resolvers_data = []
                for r in res_raw:
                    ns = await list_resolver_nameservers(session, r.id)
                    resolvers_data.append((r, ns))

                peers_raw = await list_peer_sections(session)
                peers_data = []
                for p in peers_raw:
                    entries = await list_peer_entries(session, p.id)
                    peers_data.append((p, entries))

                mailers_raw = await list_mailer_sections(session)
                mailers_data = []
                for m in mailers_raw:
                    entries = await list_mailer_entries(session, m.id)
                    mailers_data.append((m, entries))

                he_raw = await list_http_errors_sections(session)
                http_errors_data = []
                for he in he_raw:
                    entries = await list_http_error_entries(session, he.id)
                    http_errors_data.append((he, entries))

                caches_data = await list_cache_sections(session)

                config_text = generate_config(
                    global_settings=gs,
                    default_settings=ds,
                    listen_blocks=listen_blocks,
                    userlists=userlists,
                    frontends=frontends,
                    backends=backends,
                    resolvers=resolvers_data,
                    peers=peers_data,
                    mailers=mailers_data,
                    http_errors=http_errors_data,
                    caches=caches_data,
                )

                mount_dir.mkdir(parents=True, exist_ok=True)
                config_path = mount_dir / "haproxy.cfg"
                config_path.write_text(config_text)
                last_hash = latest.hash
                logger.info("Config regenerated to %s (version %s)", config_path, latest.hash[:8])

        except asyncio.CancelledError:
            logger.info("Config mount watcher task cancelled")
            break
        except Exception:
            logger.exception("Error in config mount watcher")
            await asyncio.sleep(5)
