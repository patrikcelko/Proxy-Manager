"""
SSL Certificates routes
=======================
"""

import shlex
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from proxy_manager.api.dependencies import DBSession
from proxy_manager.api.schemas.common import MessageResponse
from proxy_manager.api.schemas.ssl_certificates import (
    CertbotCommandResponse,
    SslCertificateCreate,
    SslCertificateListResponse,
    SslCertificateResponse,
    SslCertificateUpdate,
)
from proxy_manager.database.models.acl_rule import AclRule
from proxy_manager.database.models.ssl_certificate import (
    SslCertificate,
    create_ssl_certificate,
    delete_ssl_certificate,
    get_ssl_certificate,
    get_ssl_certificate_by_domain,
    list_ssl_certificates,
    update_ssl_certificate,
)

router = APIRouter(tags=["ssl-certificates"])


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string, returning None on empty/invalid."""

    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _build_certbot_command(cert: SslCertificate) -> str:
    """Build the certbot CLI command for a certificate record."""

    parts: list[str] = ["certbot", "certonly"]

    # Challenge type
    if cert.challenge_type == "standalone":
        parts.append("--standalone")
    elif cert.challenge_type == "dns-01":
        if cert.dns_plugin:
            parts.extend(["--dns-" + cert.dns_plugin])
        else:
            parts.append("--manual")
            parts.append("--preferred-challenges=dns")
    else:
        parts.append("--webroot")
        parts.extend(["-w", "/var/lib/letsencrypt"])

    # Domains
    parts.extend(["-d", cert.domain])
    if cert.alt_domains:
        for alt in cert.alt_domains.split(","):
            alt = alt.strip()
            if alt:
                parts.extend(["-d", alt])

    # Email / agree TOS
    if cert.email:
        parts.extend(["--email", cert.email])
    else:
        parts.append("--register-unsafely-without-email")
    parts.append("--agree-tos")
    parts.append("--non-interactive")

    # Cert paths (overrides)
    if cert.cert_path:
        parts.extend(["--cert-path", cert.cert_path])
    if cert.key_path:
        parts.extend(["--key-path", cert.key_path])
    if cert.fullchain_path:
        parts.extend(["--fullchain-path", cert.fullchain_path])

    return " ".join(shlex.quote(p) for p in parts)


def _build_renew_command(cert: SslCertificate) -> str:
    """Build the certbot renew command for a specific certificate."""

    parts: list[str] = [
        "certbot",
        "renew",
        "--cert-name",
        cert.domain,
        "--non-interactive",
    ]
    return " ".join(shlex.quote(p) for p in parts)


def _build_revoke_command(cert: SslCertificate) -> str:
    """Build the certbot revoke command."""

    cert_file = cert.fullchain_path or f"/etc/letsencrypt/live/{cert.domain}/fullchain.pem"
    parts: list[str] = [
        "certbot",
        "revoke",
        "--cert-path",
        cert_file,
        "--non-interactive",
    ]

    return " ".join(shlex.quote(p) for p in parts)


@router.get("/api/ssl-certificates/acl-domains")
async def api_acl_domains(session: DBSession) -> dict[str, list[str]]:
    """Return unique domains from ACL rules for the domain picker."""

    result = await session.execute(
        select(AclRule.domain).distinct().order_by(AclRule.domain),
    )
    domains = [row[0] for row in result.all() if row[0]]

    return {"domains": domains}


@router.get("/api/ssl-certificates", response_model=SslCertificateListResponse)
async def api_list_ssl_certificates(session: DBSession) -> SslCertificateListResponse:
    """List all SSL certificate records."""

    items = await list_ssl_certificates(session)
    return SslCertificateListResponse(
        count=len(items),
        items=[SslCertificateResponse.model_validate(c) for c in items],
    )


@router.get("/api/ssl-certificates/{cert_id}", response_model=SslCertificateResponse)
async def api_get_ssl_certificate(cert_id: int, session: DBSession) -> SslCertificateResponse:
    """Get a single SSL certificate by ID."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    return SslCertificateResponse.model_validate(c)


@router.post("/api/ssl-certificates", response_model=SslCertificateResponse, status_code=201)
async def api_create_ssl_certificate(
    body: SslCertificateCreate,
    session: DBSession,
) -> SslCertificateResponse:
    """Create a new SSL certificate record."""

    existing = await get_ssl_certificate_by_domain(session, body.domain)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"SSL certificate for domain '{body.domain}' already exists",
        )

    data = body.model_dump(exclude_unset=True)
    for dt_field in ("issued_at", "expires_at"):
        if dt_field in data:
            data[dt_field] = _parse_dt(data[dt_field])
    c = await create_ssl_certificate(session, **data)

    return SslCertificateResponse.model_validate(c)


@router.put("/api/ssl-certificates/{cert_id}", response_model=SslCertificateResponse)
async def api_update_ssl_certificate(
    cert_id: int,
    body: SslCertificateUpdate,
    session: DBSession,
) -> SslCertificateResponse:
    """Update an SSL certificate record."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    data = body.model_dump(exclude_unset=True)
    for dt_field in ("issued_at", "expires_at", "last_renewal_at"):
        if dt_field in data:
            data[dt_field] = _parse_dt(data[dt_field])

    c = await update_ssl_certificate(session, c, **data)
    return SslCertificateResponse.model_validate(c)


@router.delete("/api/ssl-certificates/{cert_id}", response_model=MessageResponse)
async def api_delete_ssl_certificate(cert_id: int, session: DBSession) -> MessageResponse:
    """Delete an SSL certificate record."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    await delete_ssl_certificate(session, c)
    return MessageResponse(detail="SSL certificate deleted")


@router.get(
    "/api/ssl-certificates/{cert_id}/certbot-command",
    response_model=CertbotCommandResponse,
)
async def api_certbot_command(cert_id: int, session: DBSession) -> CertbotCommandResponse:
    """Generate the Certbot CLI command for obtaining this certificate."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    cmd = _build_certbot_command(c)
    return CertbotCommandResponse(
        command=cmd,
        description=f"Certbot command to obtain certificate for {c.domain}",
    )


@router.get(
    "/api/ssl-certificates/{cert_id}/renew-command",
    response_model=CertbotCommandResponse,
)
async def api_renew_command(cert_id: int, session: DBSession) -> CertbotCommandResponse:
    """Generate the Certbot renew command for this certificate."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    cmd = _build_renew_command(c)
    return CertbotCommandResponse(
        command=cmd,
        description=f"Certbot renewal command for {c.domain}",
    )


@router.get(
    "/api/ssl-certificates/{cert_id}/revoke-command",
    response_model=CertbotCommandResponse,
)
async def api_revoke_command(cert_id: int, session: DBSession) -> CertbotCommandResponse:
    """Generate the Certbot revoke command for this certificate."""

    c = await get_ssl_certificate(session, cert_id)
    if not c:
        raise HTTPException(status_code=404, detail="SSL certificate not found")

    cmd = _build_revoke_command(c)
    return CertbotCommandResponse(
        command=cmd,
        description=f"Certbot revoke command for {c.domain}",
    )
