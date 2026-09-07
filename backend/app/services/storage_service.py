"""Blob storage behind a small interface, so swapping local disk for S3 later
is a new class, not a rewrite (PRD §4.3). Files are keyed by a server-
generated UUID; the caller's filename is never used as a path component.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import get_settings


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, data: bytes, *, suffix: str = "") -> str:
        """Persist `data` and return an opaque storage key."""

    @abstractmethod
    async def read(self, storage_key: str) -> bytes:
        """Return the bytes for a previously saved storage key."""

    @abstractmethod
    async def delete(self, storage_key: str) -> None: ...


class LocalDiskStorage(StorageBackend):
    """Default backend: files under `settings.storage_dir`, named by UUID."""

    def __init__(self, base_dir: str | None = None) -> None:
        self._base = Path(base_dir or get_settings().storage_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, *, suffix: str = "") -> str:
        key = f"{uuid.uuid4()}{suffix}"
        (self._base / key).write_bytes(data)
        return key

    async def read(self, storage_key: str) -> bytes:
        return (self._base / storage_key).read_bytes()

    async def delete(self, storage_key: str) -> None:
        path = self._base / storage_key
        if path.exists():
            path.unlink()


class S3Storage(StorageBackend):  # pragma: no cover - stub for future use
    """Not implemented — placeholder documenting the intended swap point
    (PRD §4.3). Wire up boto3 here when a real object store is needed."""

    def __init__(self, *, bucket: str) -> None:
        self._bucket = bucket

    async def save(self, data: bytes, *, suffix: str = "") -> str:
        raise NotImplementedError("S3Storage is a stub; use LocalDiskStorage")

    async def read(self, storage_key: str) -> bytes:
        raise NotImplementedError("S3Storage is a stub; use LocalDiskStorage")

    async def delete(self, storage_key: str) -> None:
        raise NotImplementedError("S3Storage is a stub; use LocalDiskStorage")


def get_storage_backend() -> StorageBackend:
    return LocalDiskStorage()
