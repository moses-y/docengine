"""Shared pytest fixtures.

Unit tests (`test_sanitize.py`, `test_docx_import.py`, `test_permissions.py`)
need no database at all — they exercise pure functions or monkeypatch the
one repository call `require_role` makes. Only `tests/integration/` spins up
a real Postgres via testcontainers, matching PRD §8.
"""

from __future__ import annotations

import uuid

import pytest


@pytest.fixture
def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
