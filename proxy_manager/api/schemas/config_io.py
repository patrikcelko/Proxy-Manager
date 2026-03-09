"""
Config import/export schemas
=============================

Request/response schemas for configuration import, export, and overview.
"""

from pydantic import BaseModel, Field


class ConfigImportRequest(BaseModel):
    """Payload for importing HAProxy configuration text."""

    config_text: str = Field(..., min_length=1)
    """Raw HAProxy configuration text."""

    merge: bool = Field(default=False, description='If true, merge with existing; if false, replace all')
    """Merge with existing config instead of replacing."""


class ConfigExportResponse(BaseModel):
    """Exported HAProxy configuration text."""

    config_text: str
    """Raw HAProxy configuration text."""


class OverviewResponse(BaseModel):
    """Dashboard overview with counts and summaries."""

    global_settings: int
    """Number of global settings."""

    default_settings: int
    """Number of default settings."""

    userlists: int
    """Number of userlists."""

    frontends: int
    """Number of frontends."""

    acl_rules: int
    """Number of ACL rules."""

    backends: int
    """Number of backends."""

    backend_servers: int
    """Number of backend servers."""

    listen_blocks: int
    """Number of listen blocks."""

    resolvers: int = 0
    """Number of resolvers."""

    peers: int = 0
    """Number of peer sections."""

    mailers: int = 0
    """Number of mailer sections."""

    http_errors: int = 0
    """Number of http-errors sections."""

    caches: int = 0
    """Number of cache sections."""

    ssl_certificates: int = 0
    """Number of SSL certificates."""
