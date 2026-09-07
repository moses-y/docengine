"""Queries against the ATTACHMENTS table."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


class AttachmentRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        document_id: UUID,
        uploaded_by: UUID,
        filename: str,
        storage_key: str,
        mime_type: str,
        size_bytes: int,
    ) -> Attachment:
        row = Attachment(
            document_id=document_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_key=storage_key,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_for_document(self, document_id: UUID) -> list[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.document_id == document_id)
            .order_by(Attachment.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, attachment_id: UUID) -> Attachment | None:
        return await self.db.get(Attachment, attachment_id)
