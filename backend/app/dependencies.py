"""FastAPI dependencies shared across routers: the current-user resolver.

Accepts the token from either the `access_token` httpOnly cookie (set by the
web app) or a `Bearer` Authorization header (for API clients / tests), so
the same routes work for both (PRD §4.1).
"""

from __future__ import annotations

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token
from app.services.auth_service import get_current_user
from app.services.errors import UnauthorizedError


def _extract_token(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if access_token:
        return access_token
    raise UnauthorizedError("Missing or invalid authentication token")


async def get_current_user_dependency(
    token: str = Depends(_extract_token), db: AsyncSession = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise UnauthorizedError("Missing or invalid authentication token")
    return await get_current_user(db, user_id)
