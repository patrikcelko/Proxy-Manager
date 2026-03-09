"""
Tests AclRuleModel CRUD
=======================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.acl_rule import (
    create_acl_rule,
    delete_all_acl_rules,
    list_all_acl_rules,
)
from proxy_manager.database.models.frontend import create_frontend


async def test_create_without_frontend(session: AsyncSession) -> None:
    """Create an ACL rule without frontend association."""

    rule = await create_acl_rule(session, frontend_id=None, domain='example.com', backend_name='be_web')
    assert rule.frontend_id is None
    assert rule.domain == 'example.com'


async def test_create_with_frontend(session: AsyncSession) -> None:
    """Create an ACL rule associated with a frontend."""

    fe = await create_frontend(session, name='fe')
    rule = await create_acl_rule(session, frontend_id=fe.id, domain='site.com', backend_name='be_site')
    assert rule.frontend_id == fe.id


async def test_delete_all(session: AsyncSession) -> None:
    """Delete all ACL rules at once."""

    await create_acl_rule(session, frontend_id=None, domain='a.com', backend_name='be_a')
    await create_acl_rule(session, frontend_id=None, domain='b.com', backend_name='be_b')
    await delete_all_acl_rules(session)

    assert len(await list_all_acl_rules(session)) == 0
