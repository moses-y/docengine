"""Password hashing and JWT issuance/verification.

Kept separate from `services/auth_service.py` so the cryptographic primitives
have zero knowledge of the database or HTTP layers — easy to unit test and
easy to swap (e.g. rotate JWT_SECRET) without touching business logic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.config import get_settings

_settings = get_settings()
_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: UUID) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    token = jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])
    except JWTError:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        return UUID(sub)
    except ValueError:
        return None
