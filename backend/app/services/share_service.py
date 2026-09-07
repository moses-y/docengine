"""Sharing business logic — grant, list, and revoke access.

Every action here requires `owner` role on the document (PRD §4.4): only the
owner can see or change who has access. Granting to an unknown email raises
`NotFoundError` rather than silently creating an invite, because invite-by-
email is explicitly out of scope for this version.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.share import ShareRole
from app.repositories.document_repo import DocumentRepo
from app.repositories.share_repo import ShareRepo
from app.repositories.user_repo import UserRepo
from app.services.errors import NotFoundError, ValidationFailedError
from app.services.permission_service import require_role


async def list_shares(db: AsyncSession, *, document_id: UUID, user_id: UUID) -> list[tuple]:
    await require_role(db, document_id=document_id, user_id=user_id, minimum="owner")
    return await ShareRepo(db).list_for_document(document_id)


async def grant_share(db: AsyncSession, *, document_id: UUID, user_id: UUID, email: str, role: str):
    await require_role(db, document_id=document_id, user_id=user_id, minimum="owner")

    doc_repo = DocumentRepo(db)
    doc = await doc_repo.get_raw(document_id)
    assert doc is not None

    target = await UserRepo(db).get_by_email(email)
    if target is None:
        raise NotFoundError("No user with that email", field="email")
    if target.id == doc.owner_id:
        raise ValidationFailedError("The owner already has full access", field="email")

    share = await ShareRepo(db).upsert(
        document_id=document_id,
        user_id=target.id,
        role=ShareRole(role),
        granted_by=user_id,
    )
    return share, target


async def revoke_share(
    db: AsyncSession, *, document_id: UUID, user_id: UUID, target_user_id: UUID
) -> None:
    await require_role(db, document_id=document_id, user_id=user_id, minimum="owner")
    revoked = await ShareRepo(db).revoke(document_id, target_user_id)
    if not revoked:
        raise NotFoundError("No share grant found for that user")
