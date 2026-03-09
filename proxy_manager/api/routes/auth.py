"""
Authentication routes
=====================
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import CurrentUser, get_current_user
from proxy_manager.api.schemas.auth import (
    ProfileUpdateRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from proxy_manager.database.connection import get_session
from proxy_manager.database.models.user import (
    User,
    count_users,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    user_exists,
)
from proxy_manager.utilities.auth import create_access_token, hash_password, verify_password
from proxy_manager.utilities.rate_limit import RATE_LIMIT_AUTH, limiter

router = APIRouter(prefix='/auth', tags=['auth'])


@router.get('/setup-required')
async def setup_required(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, bool]:
    """Check whether the application needs first-time user setup (no users exist)."""

    total = await count_users(session)
    return {'setup_required': total == 0}


@router.post('/register', response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def register(
    user_data: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> TokenResponse:
    """Register a new user and return a JWT token.

    When no users exist (first-run), anyone can register.
    Otherwise, only authenticated users can create new accounts.
    """

    total = await count_users(session)
    if total > 0:
        # Require authentication for subsequent registrations
        from proxy_manager.utilities.auth import decode_access_token

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only authenticated users can create new accounts',
            )
        token = auth_header.removeprefix('Bearer ').strip()
        user_id = decode_access_token(token)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token',
            )
        caller = await get_user_by_id(session, user_id)
        if not caller:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found',
            )

    if await user_exists(session, user_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')

    password_hash = hash_password(user_data.password)
    user = await create_user(session, email=user_data.email, name=user_data.name, password_hash=password_hash)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type='bearer', user=UserResponse.model_validate(user))  # noqa: S106


@router.post('/login', response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def login(
    credentials: UserLoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> TokenResponse:
    """Authenticate a user and return a JWT token."""

    user = await get_user_by_email(session, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type='bearer', user=UserResponse.model_validate(user))  # noqa


@router.patch('/profile', response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Update the authenticated user's profile."""

    if request.email is not None and request.email != user.email:
        if await user_exists(session, request.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')

        user.email = request.email

    if request.name is not None:
        user.name = request.name

    if request.new_password is not None:
        if request.current_password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current password required')

        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid current password')

        user.password_hash = hash_password(request.new_password)

    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.get('/me', response_model=UserResponse)
async def get_current_user_info(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the authenticated user's profile."""

    return UserResponse.model_validate(user)


@router.get('/users', response_model=list[UserResponse])
async def list_all_users(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserResponse]:
    """Return all registered users (authenticated only)."""

    users = await list_users(session)
    return [UserResponse.model_validate(u) for u in users]


@router.delete('/users/{user_id}', response_model=dict[str, str])
async def delete_user_by_id(
    user_id: int,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Delete a user by ID (authenticated only, cannot delete yourself)."""

    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot delete your own account')

    target = await get_user_by_id(session, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    await delete_user(session, target)
    return {'detail': 'User deleted'}


class AdminPasswordResetRequest(BaseModel):
    """Payload for an admin resetting another user's password."""

    new_password: str = Field(..., min_length=6)


@router.patch('/users/{user_id}/password', response_model=dict[str, str])
async def admin_reset_password(
    user_id: int,
    body: AdminPasswordResetRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Reset another user's password (admin action, cannot reset own)."""

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Use the profile endpoint to change your own password',
        )

    target = await get_user_by_id(session, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    target.password_hash = hash_password(body.new_password)
    await session.commit()
    return {'detail': 'Password updated'}
