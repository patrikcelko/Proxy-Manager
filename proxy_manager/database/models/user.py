"""
User model
==========
"""

import datetime

from sqlalchemy import DateTime, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from proxy_manager.database.models.base import Base


class User(Base):
    """Application user for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Primary key."""

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    """Unique email address."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    """Unique name identifier."""

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    """Bcrypt-hashed password."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    """Record creation timestamp."""

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""

        return f"<User(id={self.id}, email={self.email!r})>"


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address."""

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Fetch a user by primary key."""

    return await session.get(User, user_id)


async def user_exists(session: AsyncSession, email: str) -> bool:
    """Check whether a user with the given email exists."""

    stmt = select(User.id).where(User.email == email)
    result = await session.execute(stmt)

    return result.scalar_one_or_none() is not None


async def create_user(session: AsyncSession, *, email: str, name: str, password_hash: str) -> User:
    """Create and persist a new user."""

    user = User(email=email, name=name, password_hash=password_hash)
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user
