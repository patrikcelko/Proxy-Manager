"""
Mailer schemas
==============

Request/response schemas for mailer sections and their entries.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MailerEntryCreate(BaseModel):
    """Payload for creating a mailer entry."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    address: str = Field(..., min_length=1)
    """Server IP address or hostname."""

    port: int = Field(default=25, ge=1, le=65535)
    """Server port number."""

    smtp_auth: bool = False
    """Enable SMTP authentication."""

    smtp_user: str | None = None
    """SMTP authentication username."""

    smtp_password: str | None = None
    """SMTP authentication password."""

    use_tls: bool = False
    """Enable TLS for SMTP connections."""

    use_starttls: bool = False
    """Enable STARTTLS upgrade for SMTP."""

    sort_order: int = 0
    """Display ordering index."""


class MailerEntryUpdate(BaseModel):
    """Payload for updating a mailer entry."""

    name: str | None = None
    """Unique name identifier."""

    address: str | None = None
    """Server IP address or hostname."""

    port: int | None = Field(default=None, ge=1, le=65535)
    """Server port number."""

    smtp_auth: bool | None = None
    """Enable SMTP authentication."""

    smtp_user: str | None = None
    """SMTP authentication username."""

    smtp_password: str | None = None
    """SMTP authentication password."""

    use_tls: bool | None = None
    """Enable TLS for SMTP connections."""

    use_starttls: bool | None = None
    """Enable STARTTLS upgrade for SMTP."""

    sort_order: int | None = None
    """Display ordering index."""


class MailerEntryResponse(BaseModel):
    """A single mailer entry returned by the API."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    mailer_section_id: int
    """Foreign key to the parent mailer section."""

    name: str
    """Unique name identifier."""

    address: str
    """Server IP address or hostname."""

    port: int
    """Server port number."""

    smtp_auth: bool
    """Enable SMTP authentication."""

    smtp_user: str | None
    """SMTP authentication username."""

    has_smtp_password: bool = False
    """Whether an SMTP password is configured (password itself is never exposed)."""

    use_tls: bool
    """Enable TLS for SMTP connections."""

    use_starttls: bool
    """Enable STARTTLS upgrade for SMTP."""

    sort_order: int
    """Display ordering index."""

    @model_validator(mode='before')
    @classmethod
    def _hide_smtp_password(cls, data: object) -> object:
        """Replace smtp_password with a boolean flag to avoid credential leaks."""

        if isinstance(data, dict):
            data['has_smtp_password'] = bool(data.get('smtp_password'))
            data.pop('smtp_password', None)
        else:
            pw = getattr(data, 'smtp_password', None)
            object.__setattr__(data, 'has_smtp_password', bool(pw))
        return data


class MailerSectionCreate(BaseModel):
    """Payload for creating a new mailer section."""

    name: str = Field(..., min_length=1, max_length=255)
    """Unique name identifier."""

    timeout_mail: str | None = None
    """Timeout for SMTP mail delivery."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class MailerSectionUpdate(BaseModel):
    """Payload for updating an existing mailer section."""

    name: str | None = None
    """Unique name identifier."""

    timeout_mail: str | None = None
    """Timeout for SMTP mail delivery."""

    comment: str | None = None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""


class MailerSectionDetailResponse(BaseModel):
    """Mailer section with its mailer entries."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    """Primary key."""

    name: str
    """Unique name identifier."""

    timeout_mail: str | None
    """Timeout for SMTP mail delivery."""

    comment: str | None
    """Optional user comment."""

    extra_options: str | None = None
    """Additional HAProxy directives (free-form text)."""

    entries: list[MailerEntryResponse] = []
    """Child entries."""


class MailerSectionListResponse(BaseModel):
    """Paginated list of mailer sections."""

    count: int
    """Total number of items."""

    items: list[MailerSectionDetailResponse]
    """List of result items."""
