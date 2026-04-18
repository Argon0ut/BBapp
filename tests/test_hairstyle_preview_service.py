from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio

from src.models.client_photos import ClientPhotoType
from src.models.hairstyle_preview_request import HairstylePreviewStatus
from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.hairstyle_preview_service import HairstylePreviewService


class StubClientPhotoService:
    def __init__(self):
        self.last_selected_photo_types = None

    async def get_status(self, user_id: int) -> dict:
        return {"partially_completed": True}

    async def get_provider_photo_urls(self, user_id: int, selected_photo_types=None) -> list[str]:
        self.last_selected_photo_types = selected_photo_types
        return [
            "https://storage.example/front.jpg",
            "https://storage.example/right.jpg",
        ]


class StubHiggsfieldClient:
    def __init__(self, status_payload: dict | None = None):
        self.status_payload = status_payload or {}
        self.last_generate_call = None

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str,
        resolution: str,
        webhook_url: str | None,
        image_urls: list[str] | None = None,
    ) -> dict:
        self.last_generate_call = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "webhook_url": webhook_url,
            "image_urls": image_urls,
        }
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

    async def refresh_managed_storage_url(
        self,
        stored_value: str | None,
        *,
        expected_prefix: str | None = None,
    ) -> str | None:
        if stored_value == "https://bb-app-s3.s3.eu-north-1.amazonaws.com/generated-images/preview_1.jpg":
            return "https://cdn.example/generated/1.jpg"
        return stored_value


@pytest_asyncio.fixture(autouse=True)
async def clean_preview_repo():
    repo = HairstylePreviewRepository()
    await repo.clear()
    yield
    await repo.clear()


def _build_service(status_payload: dict | None = None) -> tuple[HairstylePreviewService, HairstylePreviewRepository]:
    repo = HairstylePreviewRepository()
    higgsfield_client = StubHiggsfieldClient(status_payload=status_payload)
    client_photo_service = StubClientPhotoService()
    settings = SimpleNamespace(
        public_base_url="https://app.example.com",
        has_higgsfield_credentials=True,
        s3_generated_photo_prefix="generated-images",
    )
    service = HairstylePreviewService(
        repo=repo,
        client_photo_service=client_photo_service,
        higgsfield_client=higgsfield_client,
        image_storage_service=StubImageStorageService(),
        settings=settings,
    )
    return service, repo, higgsfield_client, client_photo_service


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
    service, repo, _, _ = _build_service()
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
    service, repo, _, _ = _build_service(
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


@pytest.mark.asyncio
async def test_create_preview_passes_uploaded_photo_urls_to_higgsfield():
    service, _, higgsfield_client, _ = _build_service()

    preview = await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
    )

    assert preview["status"] == HairstylePreviewStatus.QUEUED
    call = higgsfield_client.last_generate_call
    assert call["aspect_ratio"] == "1:1"
    assert call["resolution"] == "720p"
    assert call["webhook_url"] == (
        "https://app.example.com/hairstyle-previews/webhooks/higgsfield-image"
    )
    assert call["image_urls"] == [
        "https://storage.example/front.jpg",
        "https://storage.example/right.jpg",
    ]
    assert "Identity reference only" in call["prompt"]
    assert "2 attached photos" in call["prompt"]
    assert "front-facing head-and-shoulders portrait" in call["prompt"]
    assert "Do NOT render the back or side of the head" in call["prompt"]
    assert call["prompt"].endswith(
        "New hairstyle to render on this person: short bob haircut"
    )


@pytest.mark.asyncio
async def test_get_preview_refreshes_managed_s3_urls():
    service, repo, _, _ = _build_service()
    preview_request = _build_preview_request()
    preview_request["status"] = HairstylePreviewStatus.COMPLETED
    preview_request["generated_image_url"] = (
        "https://bb-app-s3.s3.eu-north-1.amazonaws.com/generated-images/preview_1.jpg"
    )
    await repo.add(preview_request)

    preview = await service.get_preview(1)

    assert preview["generated_image_url"] == "https://cdn.example/generated/1.jpg"


@pytest.mark.asyncio
async def test_create_preview_passes_selected_photo_types_to_client_photo_service():
    service, _, _, client_photo_service = _build_service()

    await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
        selected_photo_types=[ClientPhotoType.FRONT, ClientPhotoType.REAR],
    )

    assert client_photo_service.last_selected_photo_types == [
        ClientPhotoType.FRONT,
        ClientPhotoType.REAR,
    ]
