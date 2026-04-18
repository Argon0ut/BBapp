from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio

from src.models.hairstyle_preview_request import HairstylePreviewStatus
from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.hairstyle_preview_service import HairstylePreviewService


class StubClientPhotoService:
    async def get_status(self, user_id: int) -> dict:
        return {"partially_completed": True}


class StubHiggsfieldClient:
    def __init__(self, status_payload: dict | None = None):
        self.status_payload = status_payload or {}

    async def generate_image(self, prompt: str, aspect_ratio: str, resolution: str, webhook_url: str | None) -> dict:
        return {
            "request_id": "req-1",
            "status": "queued",
            "status_url": "https://platform.higgsfield.ai/requests/req-1/status",
            "cancel_url": "https://platform.higgsfield.ai/requests/req-1/cancel",
        }

    async def get_request_status(self, status_url: str) -> dict:
        return self.status_payload

    async def cancel_image(self, cancel_url: str) -> dict:
        return {"ok": True}


class StubImageStorageService:
    async def mirror_generated_image(self, preview_id: int, source_url: str) -> str:
        return f"https://cdn.example/generated/{preview_id}.jpg"


@pytest_asyncio.fixture(autouse=True)
async def clean_preview_repo():
    repo = HairstylePreviewRepository()
    await repo.clear()
    yield
    await repo.clear()


def _build_service(status_payload: dict | None = None) -> tuple[HairstylePreviewService, HairstylePreviewRepository]:
    repo = HairstylePreviewRepository()
    settings = SimpleNamespace(
        public_base_url="https://app.example.com",
        has_higgsfield_credentials=True,
    )
    service = HairstylePreviewService(
        repo=repo,
        client_photo_service=StubClientPhotoService(),
        higgsfield_client=StubHiggsfieldClient(status_payload=status_payload),
        image_storage_service=StubImageStorageService(),
        settings=settings,
    )
    return service, repo


def _build_preview_request() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "user_id": 42,
        "text_prompt": "short bob haircut",
        "status": HairstylePreviewStatus.QUEUED,
        "aspect_ratio": "1:1",
        "resolution": "720p",
        "generation_count": 1,
        "provider_request_id": "req-1",
        "status_url": "https://platform.higgsfield.ai/requests/req-1/status",
        "cancel_url": "https://platform.higgsfield.ai/requests/req-1/cancel",
        "generated_image_url": None,
        "approved_image_url": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }


@pytest.mark.asyncio
async def test_webhook_handles_top_level_completed_images():
    service, repo = _build_service()
    await repo.add(_build_preview_request())

    response = await service.handle_higgsfield_webhook(
        {
            "status": "completed",
            "request_id": "req-1",
            "images": [{"url": "https://images.example/result.jpg"}],
        }
    )

    preview = await repo.get(1)

    assert response == {"ok": True}
    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generated_image_url"] == "https://cdn.example/generated/1.jpg"
    assert preview["error"] is None


@pytest.mark.asyncio
async def test_get_preview_reconciles_provider_status_from_status_url():
    service, repo = _build_service(
        status_payload={
            "status": "completed",
            "request_id": "req-1",
            "status_url": "https://platform.higgsfield.ai/requests/req-1/status",
            "cancel_url": "https://platform.higgsfield.ai/requests/req-1/cancel",
            "images": [{"url": "https://images.example/result.jpg"}],
        }
    )
    await repo.add(_build_preview_request())

    preview = await service.get_preview(1)

    assert preview is not None
    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generated_image_url"] == "https://cdn.example/generated/1.jpg"
    assert preview["status_url"] == "https://platform.higgsfield.ai/requests/req-1/status"
