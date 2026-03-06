"""
Authentication routes
=====================
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from proxy_manager.api.dependencies import get_current_user
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
    create_user,
    get_user_by_email,
    user_exists,
)
from proxy_manager.utilities.auth import create_access_token, hash_password, verify_password
from proxy_manager.utilities.rate_limit import RATE_LIMIT_AUTH, limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def register(
    user_data: UserRegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> TokenResponse:
    """Register a new user and return a JWT token."""

    if await user_exists(session, user_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password_hash = hash_password(user_data.password)
    user = await create_user(session, email=user_data.email, name=user_data.name, password_hash=password_hash)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))  # noqa: S106


@router.post("/login", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def login(
    credentials: UserLoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> TokenResponse:
    """Authenticate a user and return a JWT token."""

    user = await get_user_by_email(session, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))  # noqa


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Update the authenticated user's profile."""

    if request.email is not None and request.email != user.email:
        if await user_exists(session, request.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user.email = request.email

    if request.name is not None:
        user.name = request.name

    if request.new_password is not None:
        if request.current_password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password required")

        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")

        user.password_hash = hash_password(request.new_password)

    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the authenticated user's profile."""

    return UserResponse.model_validate(user)
