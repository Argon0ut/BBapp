from pydantic import BaseModel
from typing import List
from src.models.hairstyle_preview_request import HairstylePreviewStatus

class HairstylePreviewPromptSchema(BaseModel):
    text_prompt: str

class HairstylePreviewRequestSchema(BaseModel):
    id: int
    client_id: int
    text_prompt: str
    result_images: List[str | None]
    # status: HairstylePreviewStatus
