"""Document request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

Role = Literal["owner", "editor", "viewer"]


class DocumentCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class DocumentUpdate(BaseModel):
    """PATCH body. `base_version` is required whenever `content` is sent —
    it is the optimistic-concurrency token described in the PRD (§4.2)."""

    title: str | None = Field(default=None, max_length=255)
    content: dict[str, Any] | None = None
    base_version: int | None = None


class DocumentSummary(BaseModel):
    id: UUID
    title: str
    owner_email: str
    my_role: Role
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(BaseModel):
    id: UUID
    title: str
    content: dict[str, Any]
    version: int
    owner_id: UUID
    owner_email: str
    my_role: Role
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ImportResult(BaseModel):
    document: DocumentDetail
    dropped_features: list[str] = Field(default_factory=list)
