"""Document CRUD, wired through `require_role` on every operation.

Concurrency: `update` takes a `base_version` from the client and rejects with
`ConflictError` (mapped to HTTP 409 by `app.main`) if `documents.version` has
already moved past it — the PRD's chosen alternative to real-time merge
(PRD §4.2, §10). Version snapshots are written every 10th save and on every
explicit flush, per PRD §5.2, to bound write amplification while still
leaving a trail for the future version-history feature (PRD §12).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.sanitize import sanitize_document
from app.repositories.document_repo import DocumentRepo
from app.repositories.version_repo import VersionRepo
from app.services.errors import ConflictError
from app.services.permission_service import require_role

_SNAPSHOT_EVERY = 10


async def create_document(
    db: AsyncSession, *, owner_id: UUID, title: str | None
) -> tuple[Any, str]:
    repo = DocumentRepo(db)
    doc = await repo.create(owner_id=owner_id, title=title)
    return doc, "owner"


async def list_documents(db: AsyncSession, *, user_id: UUID, scope: str) -> list[tuple]:
    repo = DocumentRepo(db)
    return await repo.list_for_user(user_id, scope)


async def get_document(db: AsyncSession, *, document_id: UUID, user_id: UUID):
    role = await require_role(db, document_id=document_id, user_id=user_id, minimum="viewer")
    repo = DocumentRepo(db)
    row = await repo.get_with_owner(document_id)
    assert row is not None
    doc, owner_email = row
    return doc, owner_email, role


async def update_document(
    db: AsyncSession,
    *,
    document_id: UUID,
    user_id: UUID,
    title: str | None,
    content: dict | None,
    base_version: int | None,
    flush: bool = False,
):
    role = await require_role(db, document_id=document_id, user_id=user_id, minimum="editor")
    repo = DocumentRepo(db)
    doc = await repo.get_raw(document_id)
    assert doc is not None  # require_role already proved it exists

    if content is not None:
        if base_version is None or base_version != doc.version:
            raise ConflictError(
                "This document changed elsewhere — reload to continue.",
                field="base_version",
            )
        doc.content = sanitize_document(content)
        doc.version += 1

        should_snapshot = flush or doc.version % _SNAPSHOT_EVERY == 0
        if should_snapshot:
            await VersionRepo(db).snapshot(
                document_id=doc.id, version=doc.version, content=doc.content, author_id=user_id
            )

    if title is not None:
        doc.title = title.strip() or "Untitled document"

    await db.flush()
    row = await repo.get_with_owner(document_id)
    assert row is not None
    _, owner_email = row
    return doc, owner_email, role


async def delete_document(db: AsyncSession, *, document_id: UUID, user_id: UUID) -> None:
    await require_role(db, document_id=document_id, user_id=user_id, minimum="owner")
    repo = DocumentRepo(db)
    doc = await repo.get_raw(document_id)
    assert doc is not None
    await repo.soft_delete(doc)
