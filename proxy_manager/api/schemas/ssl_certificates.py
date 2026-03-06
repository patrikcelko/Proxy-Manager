"""
SSL certificate schemas
=======================

Request/response schemas for SSL certificate records and certbot commands.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SslCertificateCreate(BaseModel):
    """Payload for creating a new SSL certificate record."""

    domain: str = Field(..., min_length=1, max_length=255)
    """Domain pattern for ACL matching."""

    alt_domains: str | None = None
    """Subject Alternative Names (comma-separated)."""

    email: str | None = None
    """Unique email address."""

    provider: str = Field(default="certbot", pattern=r"^(certbot|manual|self-signed)$")
    """Certificate provider (`certbot`, `manual`, `self-signed`)."""

    status: str = Field(default="pending", pattern=r"^(pending|active|expired|revoked|error)$")
    """Certificate status (`pending`, `active`, `expired`, etc.)."""

    cert_path: str | None = None
    """Path to the certificate file."""

    key_path: str | None = None
    """Path to the private key file."""

    fullchain_path: str | None = None
    """Path to the full certificate chain."""

    issued_at: str | None = None
    """Certificate issuance timestamp."""

    expires_at: str | None = None
    """Certificate expiry timestamp."""

    auto_renew: bool = True
    """Enable automatic renewal."""

    challenge_type: str = Field(default="http-01", pattern=r"^(http-01|dns-01|standalone)$")
    """ACME challenge type (`http-01`, `dns-01`)."""

    dns_plugin: str | None = None
    """DNS plugin for ACME challenge."""

    comment: str | None = None
    """Optional user comment."""


class SslCertificateUpdate(BaseModel):
    """Payload for updating an existing SSL certificate record."""

    domain: str | None = None
    """Domain pattern for ACL matching."""

    alt_domains: str | None = None
    """Subject Alternative Names (comma-separated)."""

    email: str | None = None
    """Unique email address."""

    provider: str | None = None
    """Certificate provider (`certbot`, `manual`, `self-signed`)."""

    status: str | None = None
    """Certificate status (`pending`, `active`, `expired`, etc.)."""

    cert_path: str | None = None
    """Path to the certificate file."""

    key_path: str | None = None
    """Path to the private key file."""

    fullchain_path: str | None = None
    """Path to the full certificate chain."""

    issued_at: str | None = None
    """Certificate issuance timestamp."""

    expires_at: str | None = None
    """Certificate expiry timestamp."""

    auto_renew: bool | None = None
    """Enable automatic renewal."""

    challenge_type: str | None = None
    """ACME challenge type (`http-01`, `dns-01`)."""

    dns_plugin: str | None = None
    """DNS plugin for ACME challenge."""

    last_renewal_at: str | None = None
    """Last renewal timestamp."""

    last_error: str | None = None
    """Last error message."""

    comment: str | None = None
    """Optional user comment."""


class SslCertificateResponse(BaseModel):
    """A single SSL certificate record returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    domain: str
    """Domain pattern for ACL matching."""

    alt_domains: str | None
    """Subject Alternative Names (comma-separated)."""

    email: str | None
    """Unique email address."""

    provider: str
    """Certificate provider (`certbot`, `manual`, `self-signed`)."""

    status: str
    """Certificate status (`pending`, `active`, `expired`, etc.)."""

    cert_path: str | None
    """Path to the certificate file."""

    key_path: str | None
    """Path to the private key file."""

    fullchain_path: str | None
    """Path to the full certificate chain."""

    issued_at: datetime | None
    """Certificate issuance timestamp."""

    expires_at: datetime | None
    """Certificate expiry timestamp."""

    auto_renew: bool
    """Enable automatic renewal."""

    challenge_type: str
    """ACME challenge type (`http-01`, `dns-01`)."""

    dns_plugin: str | None
    """DNS plugin for ACME challenge."""

    last_renewal_at: datetime | None
    """Last renewal timestamp."""

    last_error: str | None
    """Last error message."""

    comment: str | None
    """Optional user comment."""

    created_at: datetime | None
    """Record creation timestamp."""

    updated_at: datetime | None
    """Last update timestamp."""


class SslCertificateListResponse(BaseModel):
    """Paginated list of SSL certificates."""

    count: int
    """Total number of items."""

    items: list[SslCertificateResponse]
    """List of result items."""


class CertbotCommandResponse(BaseModel):
    """Generated certbot CLI commands for a certificate."""

    command: str
    """Shell command to execute."""

    description: str
    """Command description."""
