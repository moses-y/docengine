"""Sharing request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr

ShareRoleIn = Literal["viewer", "editor"]


class ShareCreate(BaseModel):
    email: EmailStr
    role: ShareRoleIn


class ShareOut(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    display_name: str
    role: ShareRoleIn
    granted_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
