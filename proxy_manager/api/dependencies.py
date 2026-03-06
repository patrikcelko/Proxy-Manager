"""
FastAPI dependencies
====================
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.database.connection import get_session
from proxy_manager.database.models.user import get_user_by_id
from proxy_manager.utilities.auth import decode_access_token

__all__ = ["DBSession", "get_current_user"]

DBSession = Annotated[AsyncSession, Depends(get_session)]

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Validate JWT token and return the authenticated user."""

    # Prevent circular import
    from proxy_manager.database.models.user import User

    token = credentials.credentials
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user: User | None = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
