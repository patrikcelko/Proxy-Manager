"""
Tests FrontendModel CRUD
========================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.frontend import (
    create_frontend,
    create_frontend_bind,
    create_frontend_option,
    list_frontend_binds,
    list_frontend_options,
    update_frontend_bind,
    update_frontend_option,
)


async def test_create_with_binds_and_options(session: AsyncSession) -> None:
    """Create a frontend with binds and options."""

    fe = await create_frontend(session, name='fe_http', default_backend='be_web', mode='http')
    await create_frontend_bind(session, frontend_id=fe.id, bind_line='*:80')
    await create_frontend_option(session, frontend_id=fe.id, directive='option httplog')

    binds = await list_frontend_binds(session, fe.id)
    opts = await list_frontend_options(session, fe.id)
    assert len(binds) == 1
    assert len(opts) == 1


async def test_update_bind(session: AsyncSession) -> None:
    """Update a frontend bind line."""

    fe = await create_frontend(session, name='fe')
    b = await create_frontend_bind(session, frontend_id=fe.id, bind_line='*:80')
    updated = await update_frontend_bind(session, b, bind_line='*:443')
    assert updated.bind_line == '*:443'


async def test_update_option(session: AsyncSession) -> None:
    """Update a frontend option directive."""

    fe = await create_frontend(session, name='fe2')
    o = await create_frontend_option(session, frontend_id=fe.id, directive='old')
    updated = await update_frontend_option(session, o, directive='new')
    assert updated.directive == 'new'
