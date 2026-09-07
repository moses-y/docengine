"""Document CRUD and import (PRD §4.2, §4.3)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_dependency
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentDetail,
    DocumentSummary,
    DocumentUpdate,
    ImportResult,
)
from app.services import document_service, import_service
from app.services.errors import UnsupportedMediaTypeError

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _to_detail(doc, owner_email: str, role: str) -> DocumentDetail:
    return DocumentDetail(
        id=doc.id,
        title=doc.title,
        content=doc.content,
        version=doc.version,
        owner_id=doc.owner_id,
        owner_email=owner_email,
        my_role=role,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post("", response_model=DocumentDetail, status_code=201)
async def create(
    body: DocumentCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    doc, role = await document_service.create_document(
        db, owner_id=current_user.id, title=body.title
    )
    return _to_detail(doc, current_user.email, role)


@router.get("", response_model=list[DocumentSummary])
async def list_documents(
    scope: Literal["owned", "shared", "all"] = Query(default="all"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    rows = await document_service.list_documents(db, user_id=current_user.id, scope=scope)
    return [
        DocumentSummary(
            id=doc.id,
            title=doc.title,
            owner_email=owner_email,
            my_role=role,
            updated_at=doc.updated_at,
        )
        for doc, owner_email, role in rows
    ]


@router.post("/import", response_model=ImportResult, status_code=201)
async def import_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    if not file.filename:
        raise UnsupportedMediaTypeError("A filename is required to determine the import format")
    doc, dropped = await import_service.import_document(
        db, owner_id=current_user.id, filename=file.filename, data=data
    )
    return ImportResult(
        document=_to_detail(doc, current_user.email, "owner"), dropped_features=dropped
    )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get(
    document_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    doc, owner_email, role = await document_service.get_document(
        db, document_id=document_id, user_id=current_user.id
    )
    return _to_detail(doc, owner_email, role)


@router.patch("/{document_id}", response_model=DocumentDetail)
async def update(
    document_id: UUID,
    body: DocumentUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    doc, owner_email, role = await document_service.update_document(
        db,
        document_id=document_id,
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        base_version=body.base_version,
    )
    return _to_detail(doc, owner_email, role)


@router.delete("/{document_id}", status_code=204)
async def delete(
    document_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    await document_service.delete_document(db, document_id=document_id, user_id=current_user.id)
