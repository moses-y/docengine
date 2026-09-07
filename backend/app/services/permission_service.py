"""The single permission gate every document route passes through.

This module is deliberately the smallest, most heavily tested piece of the
backend (see `tests/test_permissions.py`): one role hierarchy, one function
that resolves a caller's role, one function that enforces a minimum role.
Hiding buttons in the React UI is cosmetic — `require_role` is the actual
enforcement point, and it is exercised directly by the unit tests without
going through HTTP at all.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_repo import DocumentRepo
from app.services.errors import ForbiddenError, NotFoundError

# Ordered weakest to strongest. A caller with a given role may perform any
# action gated at that role or below.
_ROLE_RANK: dict[str, int] = {"viewer": 1, "editor": 2, "owner": 3}


def role_satisfies(role: str, minimum: str) -> bool:
    return _ROLE_RANK.get(role, 0) >= _ROLE_RANK.get(minimum, 999)


async def resolve_role(db: AsyncSession, *, document_id: UUID, user_id: UUID) -> str | None:
    """Returns the caller's role on the document, or None if they have no
    access at all (no ownership row, no share row) — including when the
    document does not exist or is soft-deleted."""
    repo = DocumentRepo(db)
    return await repo.role_for_user(document_id, user_id)


async def require_role(db: AsyncSession, *, document_id: UUID, user_id: UUID, minimum: str) -> str:
    """Resolve the caller's role and enforce a minimum.

    Two distinct failure modes, both decided here so no router re-implements
    the split:
      - No access at all (no ownership row, no share row, or the document
        doesn't exist / is soft-deleted) -> `NotFoundError` (404). A stranger
        must not be able to tell "no permission" from "doesn't exist"
        (PRD §5.3).
      - Some access, but below `minimum` (e.g. a viewer on an editor-only
        route, per US-11) -> `ForbiddenError` (403). The caller already knows
        the document exists, so there is nothing left to hide.
    """
    role = await resolve_role(db, document_id=document_id, user_id=user_id)
    if role is None:
        raise NotFoundError("Document not found")
    if not role_satisfies(role, minimum):
        raise ForbiddenError(f"Requires '{minimum}' access or higher")
    return role
