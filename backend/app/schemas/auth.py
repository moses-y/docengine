"""Auth request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    """Login deliberately does not use EmailStr.

    Logging in is a credential lookup, not a place to re-derive whether an
    address is well formed -- the account either exists with that exact
    address or it does not. Validating the format here only creates a way for
    accounts that exist to become unreachable: email-validator rejects
    reserved TLDs, so every seeded @ajaia.test demo account (see README) was
    refused with a 422 before the password was ever checked. Registration
    still uses EmailStr, which is where format actually matters.
    """

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        # Addresses are stored lowercase; match how they were written.
        return value.strip().lower()


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
