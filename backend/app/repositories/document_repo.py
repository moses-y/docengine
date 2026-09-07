"""Queries against the DOCUMENTS table.

`role_for_user` implements the single access-resolution query from the PRD
(§5.3): a document row joined against the caller's own share grant, returning
NULL when the caller has neither ownership nor a grant. Every other query in
this repo that lists or fetches a document reuses that same join so the rule
is defined exactly once.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.document import EMPTY_DOC, Document
from app.models.share import DocumentShare
from app.models.user import User


class DocumentRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, owner_id: UUID, title: str | None, content: dict | None = None
    ) -> Document:
        doc = Document(
            owner_id=owner_id,
            title=title or "Untitled document",
            content=content if content is not None else EMPTY_DOC,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get_raw(self, document_id: UUID) -> Document | None:
        """Fetch the row with no permission check — callers must check role first."""
        doc = await self.db.get(Document, document_id)
        if doc is None or doc.deleted_at is not None:
            return None
        return doc

    async def role_for_user(self, document_id: UUID, user_id: UUID) -> str | None:
        """Returns 'owner' | 'editor' | 'viewer' | None. Never raises."""
        from sqlalchemy import case

        stmt = (
            select(
                case(
                    (Document.owner_id == user_id, "owner"),
                    else_=DocumentShare.role,
                ).label("role")
            )
            .select_from(Document)
            .outerjoin(
                DocumentShare,
                (DocumentShare.document_id == Document.id) & (DocumentShare.user_id == user_id),
            )
            .where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
                (Document.owner_id == user_id) | (DocumentShare.id.isnot(None)),
            )
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row is None:
            return None
        value = row[0]
        return value.value if hasattr(value, "value") else value

    async def list_for_user(self, user_id: UUID, scope: str) -> list[Row]:
        """Returns rows of (Document, owner_email, my_role) for the given scope."""
        from sqlalchemy import case

        owner = aliased(User)
        role_col = case(
            (Document.owner_id == user_id, "owner"),
            else_=DocumentShare.role,
        ).label("my_role")

        stmt = (
            select(Document, owner.email.label("owner_email"), role_col)
            .join(owner, owner.id == Document.owner_id)
            .outerjoin(
                DocumentShare,
                (DocumentShare.document_id == Document.id) & (DocumentShare.user_id == user_id),
            )
            .where(Document.deleted_at.is_(None))
        )

        if scope == "owned":
            stmt = stmt.where(Document.owner_id == user_id)
        elif scope == "shared":
            stmt = stmt.where(Document.owner_id != user_id, DocumentShare.id.isnot(None))
        else:  # "all"
            stmt = stmt.where((Document.owner_id == user_id) | (DocumentShare.id.isnot(None)))

        stmt = stmt.order_by(Document.updated_at.desc())
        result = await self.db.execute(stmt)
        return result.all()

    async def get_with_owner(self, document_id: UUID) -> Row | None:
        owner = aliased(User)
        stmt = (
            select(Document, owner.email.label("owner_email"))
            .join(owner, owner.id == Document.owner_id)
            .where(Document.id == document_id, Document.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.first()

    async def soft_delete(self, document: Document) -> None:
        from sqlalchemy import func

        document.deleted_at = func.now()
        await self.db.flush()
