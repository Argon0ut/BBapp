from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    hairstyle_preview_service as hairstyle_preview_dependency,
    require_admin,
)
from src.models.auth import AuthUser
from src.schemas.hairstyle_preview_request import (
    HairstylePreviewGenerateSchema,
    HairstylePreviewRegenerateSchema,
    HairstylePreviewRequestSchema,
    PreviewActionResponseSchema,
)
from src.services.hairstyle_preview_service import HairstylePreviewService

router = APIRouter(prefix="/hairstyle-previews", tags=["Hairstyle Previews"])


@router.post("", response_model=HairstylePreviewRequestSchema)
async def create_hairstyle_preview(
    data: HairstylePreviewGenerateSchema,
    service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
    current_user: Annotated[AuthUser, Depends(require_admin())],
):
    target_user_id = data.user_id or current_user.id
    try:
        return await service.create_preview(
            user_id=target_user_id,
            prompt=data.text_prompt,
            aspect_ratio=data.aspect_ratio,
            resolution=data.resolution,
            selected_photo_types=data.selected_photo_types,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{preview_id}", response_model=HairstylePreviewRequestSchema)
async def get_hairstyle_preview(
    preview_id: int,
    service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
    current_user: Annotated[AuthUser, Depends(require_admin())],
):
    preview = await service.get_preview(preview_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Hairstyle preview not found")
    return preview


@router.post("/{preview_id}/approve", response_model=PreviewActionResponseSchema)
async def approve_hairstyle_preview(
    preview_id: int,
    service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
    current_user: Annotated[AuthUser, Depends(require_admin())],
):
    try:
        preview = await service.approve_preview(preview_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True, "message": "Preview approved", "preview": preview}


@router.post("/{preview_id}/regenerate", response_model=PreviewActionResponseSchema)
async def regenerate_hairstyle_preview(
    preview_id: int,
    data: HairstylePreviewRegenerateSchema,
    service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
    current_user: Annotated[AuthUser, Depends(require_admin())],
):
    try:
        preview = await service.regenerate_preview(
            preview_id=preview_id,
            text_prompt=data.text_prompt,
            aspect_ratio=data.aspect_ratio,
            resolution=data.resolution,
            selected_photo_types=data.selected_photo_types,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True, "message": "Preview regeneration started", "preview": preview}


@router.post("/{preview_id}/cancel", response_model=PreviewActionResponseSchema)
async def cancel_hairstyle_preview(
    preview_id: int,
    service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
    current_user: Annotated[AuthUser, Depends(require_admin())],
):
    try:
        preview = await service.cancel_preview(preview_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True, "message": "Preview cancelled", "preview": preview}
