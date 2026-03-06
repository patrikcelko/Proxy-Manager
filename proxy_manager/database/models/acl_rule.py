"""
ACL rule model
==============
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class AclRule(Base):
    """Domain-to-backend routing rule in a frontend."""

    __tablename__ = "acl_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    frontend_id: Mapped[int | None] = mapped_column(
        ForeignKey("frontends.id", ondelete="CASCADE"), nullable=True, index=True
    )
    """Foreign key to the parent frontend."""

    domain: Mapped[str] = mapped_column(String(500), nullable=False)
    """Domain pattern for ACL matching."""

    backend_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    """Target backend name for matched requests."""

    acl_match_type: Mapped[str] = mapped_column(String(50), nullable=False, default="hdr_dom")
    """ACL match function (`hdr`, `hdr_dom`, etc.)."""

    is_redirect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Whether this rule is a redirect instead of backend routing."""

    redirect_target: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """URL prefix for redirect rules."""

    redirect_code: Mapped[int] = mapped_column(Integer, nullable=False, default=308)
    """HTTP redirect status code (301, 302, etc.)."""

    comment: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    """Optional user comment."""

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Display ordering index."""

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    """Whether the rule is active."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<AclRule(id={self.id}, domain={self.domain!r}, backend={self.backend_name!r})>"


async def list_acl_rules(session: AsyncSession, frontend_id: int) -> list[AclRule]:
    """Return all ACL rules for a given frontend, ordered by sort_order."""

    stmt = select(AclRule).where(AclRule.frontend_id == frontend_id).order_by(AclRule.sort_order, AclRule.id)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def list_all_acl_rules(session: AsyncSession) -> list[AclRule]:
    """Return every ACL rule across all frontends."""

    stmt = select(AclRule).order_by(AclRule.sort_order, AclRule.id)
    result = await session.execute(stmt)

    return list(result.scalars().all())


async def get_acl_rule(session: AsyncSession, rule_id: int) -> AclRule | None:
    """Fetch a single ACL rule by primary key."""

    return await session.get(AclRule, rule_id)


async def create_acl_rule(
    session: AsyncSession,
    *,
    frontend_id: int | None = None,
    domain: str,
    backend_name: str = "",
    acl_match_type: str = "hdr_dom",
    is_redirect: bool = False,
    redirect_target: str | None = None,
    redirect_code: int = 308,
    comment: str | None = None,
    sort_order: int = 0,
    enabled: bool = True,
) -> AclRule:
    """Create and persist a new ACL rule."""

    rule = AclRule(
        frontend_id=frontend_id,
        domain=domain,
        backend_name=backend_name,
        acl_match_type=acl_match_type,
        is_redirect=is_redirect,
        redirect_target=redirect_target,
        redirect_code=redirect_code,
        comment=comment,
        sort_order=sort_order,
        enabled=enabled,
    )
    session.add(rule)

    await session.commit()
    await session.refresh(rule)

    return rule


async def update_acl_rule(
    session: AsyncSession,
    rule: AclRule,
    *,
    frontend_id: int | None = None,
    domain: str | None = None,
    backend_name: str | None = None,
    acl_match_type: str | None = None,
    is_redirect: bool | None = None,
    redirect_target: str | None = None,
    redirect_code: int | None = None,
    comment: str | None = None,
    sort_order: int | None = None,
    enabled: bool | None = None,
    fields_set: frozenset[str] | None = None,
) -> AclRule:
    """Update an existing ACL rule with the given field values."""

    if fields_set and "frontend_id" in fields_set or frontend_id is not None:
        rule.frontend_id = frontend_id

    if domain is not None:
        rule.domain = domain

    if backend_name is not None:
        rule.backend_name = backend_name

    if acl_match_type is not None:
        rule.acl_match_type = acl_match_type

    if is_redirect is not None:
        rule.is_redirect = is_redirect

    if fields_set and "redirect_target" in fields_set or redirect_target is not None:
        rule.redirect_target = redirect_target

    if redirect_code is not None:
        rule.redirect_code = redirect_code

    if fields_set and "comment" in fields_set or comment is not None:
        rule.comment = comment

    if sort_order is not None:
        rule.sort_order = sort_order

    if enabled is not None:
        rule.enabled = enabled

    await session.commit()
    await session.refresh(rule)

    return rule


async def delete_acl_rule(session: AsyncSession, rule: AclRule) -> None:
    """Delete an ACL rule from the database."""

    await session.delete(rule)
    await session.commit()


async def delete_all_acl_rules(session: AsyncSession) -> None:
    """Delete all ACL rules."""

    await session.execute(delete(AclRule))
    await session.commit()
