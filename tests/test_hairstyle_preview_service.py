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

    async def get_provider_photo_contents(
        self,
        user_id: int,
        selected_photo_types=None,
    ) -> list[tuple[bytes, str, str]]:
        self.last_selected_photo_types = selected_photo_types
        return [
            (b"front-bytes", "image/jpeg", "front.jpg"),
            (b"right-bytes", "image/png", "right.png"),
        ]


class StubOpenAIImageClient:
    def __init__(self, exc: Exception | None = None):
        self.exc = exc
        self.last_generate_call = None

    async def generate_image(
        self,
        prompt: str,
        image_contents: list[tuple[bytes, str, str]],
        aspect_ratio: str | None = None,
    ) -> dict:
        self.last_generate_call = {
            "prompt": prompt,
            "image_contents": image_contents,
            "aspect_ratio": aspect_ratio,
        }
        if self.exc:
            raise self.exc
        return {
            "content": b"generated-image-bytes",
            "content_type": "image/png",
        }


class StubImageStorageService:
    def __init__(self):
        self.last_store_call = None

    async def store_generated_image_bytes(
        self,
        preview_id: int,
        content: bytes,
        content_type: str,
    ) -> str:
        self.last_store_call = {
            "preview_id": preview_id,
            "content": content,
            "content_type": content_type,
        }
        return f"https://cdn.example/generated/{preview_id}.png"

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


def _build_service(
    openai_exc: Exception | None = None,
) -> tuple[
    HairstylePreviewService,
    HairstylePreviewRepository,
    StubOpenAIImageClient,
    StubClientPhotoService,
    StubImageStorageService,
]:
    repo = HairstylePreviewRepository()
    openai_image_client = StubOpenAIImageClient(exc=openai_exc)
    client_photo_service = StubClientPhotoService()
    image_storage_service = StubImageStorageService()
    settings = SimpleNamespace(
        s3_generated_photo_prefix="generated-images",
    )
    service = HairstylePreviewService(
        repo=repo,
        client_photo_service=client_photo_service,
        openai_image_client=openai_image_client,
        image_storage_service=image_storage_service,
        settings=settings,
    )
    return service, repo, openai_image_client, client_photo_service, image_storage_service


def _build_preview_request() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "user_id": 42,
        "text_prompt": "short bob haircut",
        "status": HairstylePreviewStatus.COMPLETED,
        "aspect_ratio": "1:1",
        "resolution": "720p",
        "generation_count": 1,
        "provider_request_id": None,
        "status_url": None,
        "cancel_url": None,
        "generated_image_url": None,
        "approved_image_url": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }


@pytest.mark.asyncio
async def test_create_preview_generates_and_stores_image_bytes():
    service, _, openai_image_client, _, image_storage_service = _build_service()

    preview = await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
    )

    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generated_image_url"] == "https://cdn.example/generated/0.png"
    assert image_storage_service.last_store_call == {
        "preview_id": 0,
        "content": b"generated-image-bytes",
        "content_type": "image/png",
    }

    call = openai_image_client.last_generate_call
    assert call["aspect_ratio"] == "1:1"
    assert call["image_contents"] == [
        (b"front-bytes", "image/jpeg", "front.jpg"),
        (b"right-bytes", "image/png", "right.png"),
    ]
    assert "HAIR-ONLY EDIT" in call["prompt"]
    assert "2 attached photos" in call["prompt"]
    assert "exact ethnicity and race" in call["prompt"]
    assert "exact skin tone and undertone" in call["prompt"]
    assert "Do NOT change ethnicity" in call["prompt"]
    assert "Do NOT swap the face" in call["prompt"]
    assert "Do NOT render the back or side of the head" in call["prompt"]
    assert "front-facing head-and-shoulders portrait" in call["prompt"]
    assert call["prompt"].endswith(
        "New hairstyle to apply (this is the ONLY thing to change): short bob haircut"
    )


@pytest.mark.asyncio
async def test_create_preview_marks_blocked_for_policy_errors():
    service, _, _, _, _ = _build_service(
        openai_exc=RuntimeError("OpenAI image generation failed: content policy violation")
    )

    preview = await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
    )

    assert preview["status"] == HairstylePreviewStatus.BLOCKED
    assert "content policy violation" in preview["error"]


@pytest.mark.asyncio
async def test_get_preview_refreshes_managed_s3_urls():
    service, repo, _, _, _ = _build_service()
    preview_request = _build_preview_request()
    preview_request["generated_image_url"] = (
        "https://bb-app-s3.s3.eu-north-1.amazonaws.com/generated-images/preview_1.jpg"
    )
    await repo.add(preview_request)

    preview = await service.get_preview(1)

    assert preview["generated_image_url"] == "https://cdn.example/generated/1.jpg"


@pytest.mark.asyncio
async def test_create_preview_passes_selected_photo_types_to_client_photo_service():
    service, _, _, client_photo_service, _ = _build_service()

    await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
        selected_photo_types=[ClientPhotoType.FRONT, ClientPhotoType.REAR],
    )

    assert client_photo_service.last_selected_photo_types == [
        ClientPhotoType.FRONT,
        ClientPhotoType.REAR,
    ]


@pytest.mark.asyncio
async def test_regenerate_preview_replaces_image_and_increments_generation_count():
    service, repo, _, _, _ = _build_service()
    await repo.add(_build_preview_request())

    preview = await service.regenerate_preview(
        preview_id=1,
        text_prompt="low taper fade",
    )

    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generation_count"] == 2
    assert preview["text_prompt"] == "low taper fade"
    assert preview["generated_image_url"] == "https://cdn.example/generated/1.png"
