"""
Version management schemas
===========================

Request/response schemas for configuration version control.
"""

from pydantic import BaseModel, Field


class VersionStatusResponse(BaseModel):
    """Application initialization status and pending change counts."""

    initialized: bool
    """Whether the application has at least one committed version."""

    has_pending: bool
    """Whether there are uncommitted changes."""

    pending_counts: dict[str, int] = Field(default_factory=dict)
    """Per-section count of pending changes (section_key → count)."""

    current_hash: str | None = None
    """Hash of the latest committed version, if any."""


class VersionSaveRequest(BaseModel):
    """Request body for committing a new version."""

    message: str = Field(..., min_length=1, max_length=500)
    """Commit message describing the changes."""


class VersionInitImportRequest(BaseModel):
    """Request body for initializing with an imported config."""

    config_text: str = Field(..., min_length=1)
    """Raw HAProxy configuration text to import."""


class VersionSummary(BaseModel):
    """Compact version info for list views."""

    hash: str
    message: str
    user_name: str
    created_at: str
    parent_hash: str | None = None


class VersionDetail(BaseModel):
    """Full version info including diff from parent."""

    hash: str
    message: str
    user_name: str
    created_at: str
    parent_hash: str | None = None
    diff: dict = Field(default_factory=dict)
    """Diff from parent version (or empty if first version)."""


class VersionListResponse(BaseModel):
    """Paginated list of versions."""

    items: list[VersionSummary]
    total: int


class PendingChangesResponse(BaseModel):
    """Detailed pending changes with per-section diffs."""

    has_pending: bool
    pending_counts: dict[str, int] = Field(default_factory=dict)
    sections: dict = Field(default_factory=dict)
    """Per-section detailed diffs (section_key → {created, deleted, updated, total})."""


class SectionRevertRequest(BaseModel):
    """Request to revert a specific section to last committed state."""

    section: str = Field(..., min_length=1)
    """Section key to revert (e.g., 'frontends', 'backends')."""
