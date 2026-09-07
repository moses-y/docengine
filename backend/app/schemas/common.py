"""Shared response envelopes used across every router."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
