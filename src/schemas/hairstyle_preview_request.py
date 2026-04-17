from datetime import datetime

from pydantic import BaseModel

from src.models.hairstyle_preview_request import HairstylePreviewStatus


class HairstylePreviewGenerateSchema(BaseModel):
    text_prompt: str
    aspect_ratio: str = "1:1"
    resolution: str = "720p"


class HairstylePreviewRegenerateSchema(BaseModel):
    text_prompt: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None


class HairstylePreviewRequestSchema(BaseModel):
    id: int
    user_id: int
    text_prompt: str
    status: HairstylePreviewStatus
    aspect_ratio: str
    resolution: str
    generation_count: int
    provider_request_id: str | None = None
    status_url: str | None = None
    cancel_url: str | None = None
    generated_image_url: str | None = None
    approved_image_url: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class PreviewActionResponseSchema(BaseModel):
    ok: bool
    message: str
    preview: HairstylePreviewRequestSchema
