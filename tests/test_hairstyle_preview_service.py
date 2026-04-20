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

    async def get_provider_photo_payloads(
        self,
        user_id: int,
        selected_photo_types=None,
    ) -> list[tuple[str, bytes, str]]:
        self.last_selected_photo_types = selected_photo_types
        return [
            ("front.png", b"front-bytes", "image/png"),
            ("right.png", b"right-bytes", "image/png"),
        ]


class StubOpenAIImageClient:
    def __init__(self, *, raise_exc: Exception | None = None):
        self.raise_exc = raise_exc
        self.last_generate_call = None

    async def generate_image(
        self,
        *,
        prompt: str,
        aspect_ratio: str,
        image_payloads: list[tuple[str, bytes, str]],
    ) -> bytes:
        self.last_generate_call = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "image_payloads": image_payloads,
        }
        if self.raise_exc:
            raise self.raise_exc
        return b"generated-png-bytes"


class StubImageStorageService:
    def __init__(self):
        self.last_store_call = None

    async def store_generated_image(
        self,
        preview_id: int,
        content: bytes,
        content_type: str = "image/png",
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
        return stored_value


@pytest_asyncio.fixture(autouse=True)
async def clean_preview_repo():
    repo = HairstylePreviewRepository()
    await repo.clear()
    yield
    await repo.clear()


def _build_service(
    *,
    openai_raise: Exception | None = None,
) -> tuple[HairstylePreviewService, HairstylePreviewRepository, StubOpenAIImageClient, StubClientPhotoService]:
    repo = HairstylePreviewRepository()
    openai_client = StubOpenAIImageClient(raise_exc=openai_raise)
    client_photo_service = StubClientPhotoService()
    settings = SimpleNamespace(
        public_base_url="https://app.example.com",
        s3_generated_photo_prefix="generated-images",
    )
    service = HairstylePreviewService(
        repo=repo,
        client_photo_service=client_photo_service,
        openai_image_client=openai_client,
        image_storage_service=StubImageStorageService(),
        settings=settings,
    )
    return service, repo, openai_client, client_photo_service


def _build_preview_request(**overrides) -> dict:
    now = datetime.now(timezone.utc)
    request = {
        "id": 1,
        "user_id": 42,
        "text_prompt": "short bob haircut",
        "status": HairstylePreviewStatus.COMPLETED,
        "aspect_ratio": "1:1",
        "resolution": "720p",
        "generation_count": 1,
        "generated_image_url": "https://cdn.example/generated/1.png",
        "approved_image_url": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    request.update(overrides)
    return request


@pytest.mark.asyncio
async def test_create_preview_sends_prompt_and_photo_bytes_to_openai():
    service, _, openai_client, _ = _build_service()

    preview = await service.create_preview(
        user_id=42,
        prompt="short bob haircut",
    )

    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generated_image_url"] == "https://cdn.example/generated/0.png"
    assert preview["error"] is None

    call = openai_client.last_generate_call
    assert call["aspect_ratio"] == "1:1"
    assert call["image_payloads"] == [
        ("front.png", b"front-bytes", "image/png"),
        ("right.png", b"right-bytes", "image/png"),
    ]
    assert "HAIR-ONLY EDIT" in call["prompt"]
    assert "2 attached photos" in call["prompt"]
    assert call["prompt"].endswith(
        "New hairstyle to apply (this is the ONLY thing to change): short bob haircut"
    )


@pytest.mark.asyncio
async def test_create_preview_marks_failure_when_openai_raises():
    service, _, _, _ = _build_service(openai_raise=RuntimeError("boom"))

    preview = await service.create_preview(
        user_id=42,
        prompt="short bob",
    )

    assert preview["status"] == HairstylePreviewStatus.FAILED
    assert preview["error"] == "boom"
    assert preview["generated_image_url"] is None


@pytest.mark.asyncio
async def test_create_preview_passes_selected_photo_types_to_client_photo_service():
    service, _, _, client_photo_service = _build_service()

    await service.create_preview(
        user_id=42,
        prompt="short bob",
        selected_photo_types=[ClientPhotoType.FRONT, ClientPhotoType.REAR],
    )

    assert client_photo_service.last_selected_photo_types == [
        ClientPhotoType.FRONT,
        ClientPhotoType.REAR,
    ]


@pytest.mark.asyncio
async def test_get_preview_returns_stored_record_without_polling():
    service, repo, _, _ = _build_service()
    await repo.add(_build_preview_request())

    preview = await service.get_preview(1)

    assert preview is not None
    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generated_image_url"] == "https://cdn.example/generated/1.png"


@pytest.mark.asyncio
async def test_approve_preview_promotes_generated_image_to_approved():
    service, repo, _, _ = _build_service()
    await repo.add(_build_preview_request())

    preview = await service.approve_preview(1)

    assert preview["status"] == HairstylePreviewStatus.APPROVED
    assert preview["approved_image_url"] == "https://cdn.example/generated/1.png"


@pytest.mark.asyncio
async def test_approve_preview_rejects_when_image_not_ready():
    service, repo, _, _ = _build_service()
    await repo.add(_build_preview_request(generated_image_url=None, status=HairstylePreviewStatus.PROCESSING))

    with pytest.raises(ValueError):
        await service.approve_preview(1)


@pytest.mark.asyncio
async def test_regenerate_preview_runs_new_generation_cycle():
    service, repo, openai_client, _ = _build_service()
    await repo.add(_build_preview_request())

    preview = await service.regenerate_preview(1, text_prompt="long curly")

    assert preview["status"] == HairstylePreviewStatus.COMPLETED
    assert preview["generation_count"] == 2
    assert preview["text_prompt"] == "long curly"
    assert openai_client.last_generate_call["prompt"].endswith(
        "New hairstyle to apply (this is the ONLY thing to change): long curly"
    )


@pytest.mark.asyncio
async def test_cancel_preview_marks_record_as_cancelled():
    service, repo, _, _ = _build_service()
    await repo.add(_build_preview_request(status=HairstylePreviewStatus.PROCESSING))

    preview = await service.cancel_preview(1)

    assert preview["status"] == HairstylePreviewStatus.CANCELLED
