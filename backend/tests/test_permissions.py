"""The require_role matrix — the single most important test in this repo
(PRD §8). It exercises the exact 404-vs-403 split described in PRD §5.3 and
US-11: a stranger with no access gets NotFoundError, and a caller with
insufficient access gets ForbiddenError, never the other way around.

`resolve_role` is monkeypatched rather than backed by a real database: the
business rule under test lives entirely in `require_role`'s branching, and a
fake role resolver lets this run anywhere (no Postgres, no event loop set up
beyond pytest-asyncio) while still testing the real function.
"""

from __future__ import annotations

import uuid

import pytest

from app.services import permission_service
from app.services.errors import ForbiddenError, NotFoundError

DOC_ID = uuid.uuid4()
USER_ID = uuid.uuid4()

# (caller's actual role or None, minimum required, expected outcome)
_MATRIX = [
    ("owner", "viewer", "allow"),
    ("owner", "editor", "allow"),
    ("owner", "owner", "allow"),
    ("editor", "viewer", "allow"),
    ("editor", "editor", "allow"),
    ("editor", "owner", "forbidden"),
    ("viewer", "viewer", "allow"),
    ("viewer", "editor", "forbidden"),
    ("viewer", "owner", "forbidden"),
    (None, "viewer", "not_found"),
    (None, "editor", "not_found"),
    (None, "owner", "not_found"),
]


class _FakeSession:
    """Never touched — `resolve_role` is monkeypatched below, so no query
    should reach a real session in this test module."""


@pytest.mark.parametrize("actual_role,minimum,expected", _MATRIX)
async def test_require_role_matrix(monkeypatch, actual_role, minimum, expected):
    async def fake_resolve_role(db, *, document_id, user_id):
        assert document_id == DOC_ID
        assert user_id == USER_ID
        return actual_role

    monkeypatch.setattr(permission_service, "resolve_role", fake_resolve_role)

    if expected == "not_found":
        with pytest.raises(NotFoundError):
            await permission_service.require_role(
                _FakeSession(), document_id=DOC_ID, user_id=USER_ID, minimum=minimum
            )
    elif expected == "forbidden":
        with pytest.raises(ForbiddenError):
            await permission_service.require_role(
                _FakeSession(), document_id=DOC_ID, user_id=USER_ID, minimum=minimum
            )
    else:
        role = await permission_service.require_role(
            _FakeSession(), document_id=DOC_ID, user_id=USER_ID, minimum=minimum
        )
        assert role == actual_role


def test_role_satisfies_ordering():
    assert permission_service.role_satisfies("owner", "viewer")
    assert permission_service.role_satisfies("owner", "editor")
    assert permission_service.role_satisfies("owner", "owner")
    assert permission_service.role_satisfies("editor", "viewer")
    assert not permission_service.role_satisfies("editor", "owner")
    assert not permission_service.role_satisfies("viewer", "editor")
    assert not permission_service.role_satisfies("unknown-role", "viewer")


async def test_stranger_and_underprivileged_viewer_are_distinguishable(monkeypatch):
    """This is US-11 written as an assertion: a viewer attempting an
    editor-only action must see a 403 (they know the doc exists), while a
    user with no grant at all must see a 404 (they should not be able to
    confirm the document exists)."""

    async def resolve_none(db, *, document_id, user_id):
        return None

    monkeypatch.setattr(permission_service, "resolve_role", resolve_none)
    with pytest.raises(NotFoundError):
        await permission_service.require_role(
            _FakeSession(), document_id=DOC_ID, user_id=USER_ID, minimum="editor"
        )

    async def resolve_viewer(db, *, document_id, user_id):
        return "viewer"

    monkeypatch.setattr(permission_service, "resolve_role", resolve_viewer)
    with pytest.raises(ForbiddenError):
        await permission_service.require_role(
            _FakeSession(), document_id=DOC_ID, user_id=USER_ID, minimum="editor"
        )
