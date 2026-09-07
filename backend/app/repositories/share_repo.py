"""Queries against the DOCUMENT_SHARES table."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.share import DocumentShare, ShareRole
from app.models.user import User


class ShareRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_document(self, document_id: UUID) -> list[Row]:
        stmt = (
            select(DocumentShare, User.email, User.display_name)
            .join(User, User.id == DocumentShare.user_id)
            .where(DocumentShare.document_id == document_id)
            .order_by(DocumentShare.created_at)
        )
        result = await self.db.execute(stmt)
        return result.all()

    async def get(self, document_id: UUID, user_id: UUID) -> DocumentShare | None:
        stmt = select(DocumentShare).where(
            DocumentShare.document_id == document_id, DocumentShare.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self, *, document_id: UUID, user_id: UUID, role: ShareRole, granted_by: UUID
    ) -> DocumentShare:
        existing = await self.get(document_id, user_id)
        if existing is not None:
            existing.role = role
            existing.granted_by = granted_by
            await self.db.flush()
            return existing
        share = DocumentShare(
            document_id=document_id, user_id=user_id, role=role, granted_by=granted_by
        )
        self.db.add(share)
        await self.db.flush()
        return share

    async def revoke(self, document_id: UUID, user_id: UUID) -> bool:
        share = await self.get(document_id, user_id)
        if share is None:
            return False
        await self.db.delete(share)
        await self.db.flush()
        return True
