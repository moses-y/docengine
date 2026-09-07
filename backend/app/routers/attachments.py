"""File attachments on an existing document (PRD §4.3, US-12)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_dependency
from app.models.user import User
from app.schemas.attachment import AttachmentOut
from app.services import import_service

router = APIRouter(prefix="/api/documents/{document_id}/attachments", tags=["attachments"])


@router.get("", response_model=list[AttachmentOut])
async def list_attachments(
    document_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    return await import_service.list_attachments(
        db, document_id=document_id, user_id=current_user.id
    )


@router.post("", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    document_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    return await import_service.add_attachment(
        db,
        document_id=document_id,
        user_id=current_user.id,
        filename=file.filename or "upload",
        data=data,
    )
