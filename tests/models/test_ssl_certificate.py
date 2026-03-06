"""
Tests SslCertificateModel CRUD
==============================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.ssl_certificate import (
    create_ssl_certificate,
    delete_all_ssl_certificates,
    delete_ssl_certificate,
    get_ssl_certificate,
    get_ssl_certificate_by_domain,
    list_ssl_certificates,
    update_ssl_certificate,
)


async def test_create_and_list(session: AsyncSession) -> None:
    """Create an SSL certificate and list all."""

    await create_ssl_certificate(session, domain="example.com", provider="certbot", status="pending")

    rows = await list_ssl_certificates(session)
    assert len(rows) == 1
    assert rows[0].domain == "example.com"


async def test_get_by_id_and_domain(session: AsyncSession) -> None:
    """Get certificate by ID and by domain."""

    cert = await create_ssl_certificate(session, domain="test.example.com")
    by_id = await get_ssl_certificate(session, cert.id)
    by_domain = await get_ssl_certificate_by_domain(session, "test.example.com")

    assert by_id is not None and by_domain is not None
    assert by_id.id == by_domain.id


async def test_update(session: AsyncSession) -> None:
    """Update certificate status and paths."""

    cert = await create_ssl_certificate(session, domain="example.com", status="pending")
    updated = await update_ssl_certificate(
        session,
        cert,
        status="active",
        cert_path="/etc/letsencrypt/live/example.com/cert.pem",
        key_path="/etc/letsencrypt/live/example.com/privkey.pem",
        fullchain_path="/etc/letsencrypt/live/example.com/fullchain.pem",
    )

    assert updated.status == "active"
    assert updated is not None and updated.cert_path is not None
    assert updated.cert_path.endswith("cert.pem")


async def test_delete(session: AsyncSession) -> None:
    """Delete a single certificate."""

    cert = await create_ssl_certificate(session, domain="temp.example.com")

    await delete_ssl_certificate(session, cert)
    assert len(await list_ssl_certificates(session)) == 0


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all certificates at once."""

    await create_ssl_certificate(session, domain="a.example.com")
    await create_ssl_certificate(session, domain="b.example.com")
    await delete_all_ssl_certificates(session)
    assert len(await list_ssl_certificates(session)) == 0


async def test_all_optional_fields(session: AsyncSession) -> None:
    """Create a certificate with every optional field populated."""

    cert = await create_ssl_certificate(
        session,
        domain="full.example.com",
        alt_domains="www.full.example.com,cdn.full.example.com",
        email="admin@example.com",
        provider="certbot",
        status="active",
        challenge_type="dns-01",
        dns_plugin="cloudflare",
        auto_renew=True,
        comment="full test cert",
    )

    fetched = await get_ssl_certificate(session, cert.id)
    assert fetched is not None
    assert fetched.alt_domains == "www.full.example.com,cdn.full.example.com"
    assert fetched.email == "admin@example.com"
    assert fetched.challenge_type == "dns-01"
    assert fetched.dns_plugin == "cloudflare"
    assert fetched.auto_renew is True
