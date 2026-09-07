"""Sharing endpoints, nested under a document (PRD §4.4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_dependency
from app.models.user import User
from app.schemas.share import ShareCreate, ShareOut
from app.services import share_service

router = APIRouter(prefix="/api/documents/{document_id}/shares", tags=["shares"])


@router.get("", response_model=list[ShareOut])
async def list_shares(
    document_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    rows = await share_service.list_shares(db, document_id=document_id, user_id=current_user.id)
    return [
        ShareOut(
            id=share.id,
            user_id=share.user_id,
            email=email,
            display_name=display_name,
            role=share.role.value,
            granted_by=share.granted_by,
            created_at=share.created_at,
        )
        for share, email, display_name in rows
    ]


@router.post("", response_model=ShareOut, status_code=201)
async def grant_share(
    document_id: UUID,
    body: ShareCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    share, target = await share_service.grant_share(
        db,
        document_id=document_id,
        user_id=current_user.id,
        email=body.email,
        role=body.role,
    )
    return ShareOut(
        id=share.id,
        user_id=share.user_id,
        email=target.email,
        display_name=target.display_name,
        role=share.role.value,
        granted_by=share.granted_by,
        created_at=share.created_at,
    )


@router.delete("/{user_id}", status_code=204)
async def revoke_share(
    document_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    await share_service.revoke_share(
        db, document_id=document_id, user_id=current_user.id, target_user_id=user_id
    )
