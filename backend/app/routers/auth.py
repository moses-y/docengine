"""Registration, login, and "who am I" (PRD §4.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user_dependency
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

_settings = get_settings()


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_settings.jwt_expire_minutes * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, token = await auth_service.register(
        db, email=body.email, display_name=body.display_name, password=body.password
    )
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, token = await auth_service.login(db, email=body.email, password=body.password)
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie("access_token")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user_dependency)):
    return UserOut.model_validate(current_user)
