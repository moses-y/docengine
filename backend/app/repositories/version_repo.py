"""Queries against the DOCUMENT_VERSIONS table.

Write-only in v1 (see PRD §12 backlog item 2 for the eventual read side)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.version import DocumentVersion


class VersionRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def snapshot(
        self, *, document_id: UUID, version: int, content: dict, author_id: UUID
    ) -> DocumentVersion:
        row = DocumentVersion(
            document_id=document_id, version=version, content=content, author_id=author_id
        )
        self.db.add(row)
        await self.db.flush()
        return row
