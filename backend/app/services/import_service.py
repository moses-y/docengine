"""File import and attachment upload orchestration (PRD §4.3).

Validation order matters: size is checked before we ever touch the bytes
with `python-magic`, and the sniffed MIME type — never the client-supplied
`Content-Type` header — decides whether we accept the file. Import only
supports `.txt`, `.md`, and `.docx`; anything else is an attachment, not an
importable document.
"""

from __future__ import annotations

from uuid import UUID

import magic
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.content.importers import docx_importer, md_importer, txt_importer
from app.models.document import Document
from app.repositories.attachment_repo import AttachmentRepo
from app.repositories.document_repo import DocumentRepo
from app.services.errors import PayloadTooLargeError, UnsupportedMediaTypeError
from app.services.permission_service import require_role
from app.services.storage_service import get_storage_backend

_IMPORT_MIME_MAP = {
    "text/plain": "txt",
    "text/markdown": "md",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


def _validate_size(data: bytes) -> None:
    limit = get_settings().max_upload_bytes
    if len(data) > limit:
        raise PayloadTooLargeError(f"File exceeds the {limit // (1024 * 1024)} MB upload limit")


def _sniff_mime(data: bytes) -> str:
    return magic.from_buffer(data, mime=True)


def _kind_from_filename_and_mime(filename: str, mime: str) -> str | None:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext in ("md", "markdown") or mime == "text/markdown":
        return "md"
    if ext == "docx" or mime == _IMPORT_MIME_MAP.get(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return "docx"
    if ext == "txt" or mime == "text/plain":
        return "txt"
    return None


async def import_document(
    db: AsyncSession, *, owner_id: UUID, filename: str, data: bytes
) -> tuple[Document, list[str]]:
    _validate_size(data)
    mime = _sniff_mime(data)
    kind = _kind_from_filename_and_mime(filename, mime)

    if kind == "txt":
        pm_doc, dropped = txt_importer.to_prosemirror(data), []
    elif kind == "md":
        pm_doc, dropped = md_importer.to_prosemirror(data), []
    elif kind == "docx":
        pm_doc, dropped = docx_importer.to_prosemirror(data)
    else:
        raise UnsupportedMediaTypeError(
            "Only .txt, .md, and .docx files can be imported as documents"
        )

    title = filename.rsplit(".", 1)[0][:255] or "Imported document"
    repo = DocumentRepo(db)
    doc = await repo.create(owner_id=owner_id, title=title, content=pm_doc)
    return doc, dropped


async def add_attachment(
    db: AsyncSession, *, document_id: UUID, user_id: UUID, filename: str, data: bytes
):
    await require_role(db, document_id=document_id, user_id=user_id, minimum="editor")
    _validate_size(data)
    mime = _sniff_mime(data)

    storage = get_storage_backend()
    suffix = f".{filename.rsplit('.', 1)[-1]}" if "." in filename else ""
    storage_key = await storage.save(data, suffix=suffix)

    repo = AttachmentRepo(db)
    return await repo.create(
        document_id=document_id,
        uploaded_by=user_id,
        filename=filename,
        storage_key=storage_key,
        mime_type=mime,
        size_bytes=len(data),
    )


async def list_attachments(db: AsyncSession, *, document_id: UUID, user_id: UUID):
    await require_role(db, document_id=document_id, user_id=user_id, minimum="viewer")
    return await AttachmentRepo(db).list_for_document(document_id)
