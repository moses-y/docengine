"""Registration and login business logic."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepo
from app.security import create_access_token, hash_password, verify_password
from app.services.errors import ConflictError, UnauthorizedError


async def register(
    db: AsyncSession, *, email: str, display_name: str, password: str
) -> tuple[User, str]:
    repo = UserRepo(db)
    if await repo.get_by_email(email) is not None:
        raise ConflictError("An account with that email already exists", field="email")
    user = await repo.create(
        email=email, display_name=display_name, password_hash=hash_password(password)
    )
    token, _ = create_access_token(user.id)
    return user, token


async def login(db: AsyncSession, *, email: str, password: str) -> tuple[User, str]:
    repo = UserRepo(db)
    user = await repo.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password")
    token, _ = create_access_token(user.id)
    return user, token


async def get_current_user(db: AsyncSession, user_id) -> User:
    repo = UserRepo(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Account no longer exists")
    return user
