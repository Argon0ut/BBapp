from datetime import datetime

from pydantic import BaseModel, model_validator

from src.models.client_photos import ClientPhotoType
from src.models.hairstyle_preview_request import HairstylePreviewStatus


class HairstylePreviewGenerateSchema(BaseModel):
    user_id: int | None = None
    text_prompt: str
    aspect_ratio: str = "1:1"
    resolution: str = "720p"
    selected_photo_types: list[ClientPhotoType] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_selected_photo_types(cls, data):
        if not isinstance(data, dict):
            return data

        if data.get("selected_photo_types") is not None:
            return data

        normalized_photo_types: list[str] = []
        for key in ("photo_types", "selected_images", "selectedPhotos", "selectedImageTypes"):
            value = data.get(key)
            if not isinstance(value, list):
                continue

            for item in value:
                if isinstance(item, str):
                    normalized_photo_types.append(item)
                    continue

                if isinstance(item, dict):
                    photo_type = item.get("photo_type") or item.get("type") or item.get("image_type")
                    if photo_type:
                        normalized_photo_types.append(photo_type)

        if normalized_photo_types:
            data["selected_photo_types"] = normalized_photo_types

        return data


class HairstylePreviewRegenerateSchema(BaseModel):
    text_prompt: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    selected_photo_types: list[ClientPhotoType] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_selected_photo_types(cls, data):
        return HairstylePreviewGenerateSchema.normalize_selected_photo_types(data)


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
