from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import hairstyle_preview_service as hairstyle_preview_dependency
from src.services.hairstyle_preview_service import HairstylePreviewService
from src.schemas.hairstyle_preview_request import (
    HairstylePreviewRequestSchema,
    HairstylePreviewPromptSchema,
)

router = APIRouter(prefix="/hairstyle-previews", tags=["Hairstyle Previews"])


@router.post("", response_model=HairstylePreviewRequestSchema)
async def create_hairstyle_preview(
        client_id: int,
        data: HairstylePreviewPromptSchema,
        service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
):
    try:
        return await service.create_preview(client_id, data.text_prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{preview_id}")
async def get_hairstyle_preview(
        preview_id: int,
        service: Annotated[HairstylePreviewService, Depends(hairstyle_preview_dependency)],
):
    preview = await service.get_preview(preview_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Hairstyle preview not found")
    return preview
