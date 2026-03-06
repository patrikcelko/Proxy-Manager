"""
Tests BackendModel CRUD
=======================
"""

from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.models.backend import (
    create_backend,
    create_backend_server,
    list_backend_servers,
)


async def test_create_with_servers(session: AsyncSession) -> None:
    """Create a backend with two servers."""

    be = await create_backend(session, name="be_web", mode="http", balance="roundrobin")
    await create_backend_server(session, backend_id=be.id, name="web1", address="10.0.0.1", port=8080)
    await create_backend_server(session, backend_id=be.id, name="web2", address="10.0.0.2", port=8080)

    servers = await list_backend_servers(session, be.id)
    assert len(servers) == 2
