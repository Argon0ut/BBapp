from datetime import datetime, timezone

from src.config import Settings
from src.models.client_photos import ClientPhotoType
from src.models.hairstyle_preview_request import HairstylePreviewStatus
from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.client_photo_service import ClientPhotoService
from src.services.image_storage_service import ImageStorageService
from src.services.openai_image_client import OpenAIImageClient

IDENTITY_PROMPT_PREFIX = (
    "This is a HAIR-ONLY EDIT of a real human photograph. The {photo_count} "
    "attached photos show ONE specific real person and are the ground truth for "
    "this person's identity. The output must be the IDENTICAL person from those "
    "photos — not a similar person, not a new person inspired by them.\n\n"
    "HARD CONSTRAINTS — the output MUST preserve, unchanged, every one of the "
    "following from the reference photos:\n"
    "- exact ethnicity and race\n"
    "- exact skin tone and undertone (do not lighten, do not darken, do not "
    "shift hue)\n"
    "- exact facial bone structure: jawline, cheekbones, chin, forehead, brow "
    "ridge\n"
    "- exact eye shape, eye color, eyelid shape and spacing\n"
    "- exact nose shape, width, bridge, and tip\n"
    "- exact lip shape, thickness, and cupid's bow\n"
    "- exact age, facial hair, moles, freckles, scars, and any other "
    "distinguishing marks\n"
    "- exact neck, shoulders, and visible body build\n\n"
    "FORBIDDEN: do NOT change ethnicity. Do NOT swap the face. Do NOT invent a "
    "new person. Do NOT blend with another person. Do NOT alter skin tone. Do "
    "NOT restyle or beautify the face. Do NOT copy the pose, crop, background, "
    "or camera angle from the references. Do NOT render the back or side of the "
    "head. Do NOT add or remove facial hair. Do NOT change the person's "
    "apparent age.\n\n"
    "ONLY permitted change: replace the hair with the hairstyle described "
    "below. Everything else in the image must remain the same real person from "
    "the references.\n\n"
    "Output: a single photorealistic front-facing head-and-shoulders portrait "
    "of this same person, eyes to camera, neutral studio background, soft even "
    "lighting, sharp focus on the face and the new hair."
)
USER_PROMPT_PREFIX = "New hairstyle to apply (this is the ONLY thing to change): "


class HairstylePreviewService:
    def __init__(
        self,
        repo: HairstylePreviewRepository,
        client_photo_service: ClientPhotoService,
        openai_image_client: OpenAIImageClient,
        image_storage_service: ImageStorageService,
        settings: Settings,
    ):
        self.preview_repo = repo
        self.client_photo_service = client_photo_service
        self.openai_image_client = openai_image_client
        self.image_storage_service = image_storage_service
        self.settings = settings

    @staticmethod
    def _compose_provider_prompt(user_prompt: str, photo_count: int) -> str:
        if photo_count <= 0:
            return user_prompt
        return (
            IDENTITY_PROMPT_PREFIX.format(photo_count=photo_count)
            + "\n\n"
            + USER_PROMPT_PREFIX
            + user_prompt.strip()
        )

    async def _refresh_preview_asset_urls(self, preview: dict | None) -> dict | None:
        if not preview:
            return preview

        refreshed_preview = dict(preview)
        for field_name in ("generated_image_url", "approved_image_url"):
            refreshed_preview[field_name] = await self.image_storage_service.refresh_managed_storage_url(
                refreshed_preview.get(field_name),
                expected_prefix=self.settings.s3_generated_photo_prefix,
            )
        return refreshed_preview

    async def _run_generation(
        self,
        preview_id: int,
        user_id: int,
        prompt: str,
        aspect_ratio: str,
        selected_photo_types: list[ClientPhotoType] | None,
    ) -> dict | None:
        try:
            photo_payloads = await self.client_photo_service.get_provider_photo_payloads(
                user_id,
                selected_photo_types=selected_photo_types,
            )
            image_bytes = await self.openai_image_client.generate_image(
                prompt=self._compose_provider_prompt(prompt, len(photo_payloads)),
                aspect_ratio=aspect_ratio,
                image_payloads=photo_payloads,
            )
            generated_url = await self.image_storage_service.store_generated_image(
                preview_id=preview_id,
                content=image_bytes,
            )
        except Exception as exc:
            failed = await self.preview_repo.update(
                preview_id,
                {
                    "status": HairstylePreviewStatus.FAILED,
                    "error": str(exc),
                    "generated_image_url": None,
                },
            )
            return await self._refresh_preview_asset_urls(failed)

        completed = await self.preview_repo.update(
            preview_id,
            {
                "status": HairstylePreviewStatus.COMPLETED,
                "generated_image_url": generated_url,
                "error": None,
            },
        )
        return await self._refresh_preview_asset_urls(completed)

    async def create_preview(
        self,
        user_id: int,
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "720p",
        selected_photo_types: list[ClientPhotoType] | None = None,
    ):
        status = await self.client_photo_service.get_status(user_id)
        if not status['partially_completed']:
            raise Exception("User photos are not ready to be loaded to AI")

        preview_id = await self.preview_repo._next_id()
        now = datetime.now(timezone.utc)
        request = {
            "id": preview_id,
            "user_id": user_id,
            "text_prompt": prompt,
            "status": HairstylePreviewStatus.PROCESSING,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "generation_count": 1,
            "generated_image_url": None,
            "approved_image_url": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.preview_repo.add(request)

        return await self._run_generation(
            preview_id=preview_id,
            user_id=user_id,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            selected_photo_types=selected_photo_types,
        )

    async def get_preview(self, preview_id: int) -> dict | None:
        preview = await self.preview_repo.get(preview_id)
        if not preview:
            return None
        return await self._refresh_preview_asset_urls(preview)

    async def approve_preview(self, preview_id: int):
        preview = await self.get_preview(preview_id)
        if not preview:
            raise ValueError("Hairstyle preview not found")
        if not preview.get("generated_image_url"):
            raise ValueError("Preview image is not ready yet")

        approved_preview = await self.preview_repo.update(
            preview_id,
            {
                "status": HairstylePreviewStatus.APPROVED,
                "approved_image_url": preview["generated_image_url"],
                "error": None,
            },
        )
        return await self._refresh_preview_asset_urls(approved_preview)

    async def regenerate_preview(
        self,
        preview_id: int,
        text_prompt: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        selected_photo_types: list[ClientPhotoType] | None = None,
    ):
        preview = await self.preview_repo.get(preview_id)
        if not preview:
            raise ValueError("Hairstyle preview not found")

        next_prompt = text_prompt or preview["text_prompt"]
        next_aspect_ratio = aspect_ratio or preview["aspect_ratio"]
        next_resolution = resolution or preview["resolution"]

        await self.preview_repo.update(
            preview_id,
            {
                "text_prompt": next_prompt,
                "aspect_ratio": next_aspect_ratio,
                "resolution": next_resolution,
                "status": HairstylePreviewStatus.PROCESSING,
                "generation_count": preview["generation_count"] + 1,
                "generated_image_url": None,
                "approved_image_url": None,
                "error": None,
            },
        )

        return await self._run_generation(
            preview_id=preview_id,
            user_id=preview["user_id"],
            prompt=next_prompt,
            aspect_ratio=next_aspect_ratio,
            selected_photo_types=selected_photo_types,
        )

    async def cancel_preview(self, preview_id: int):
        preview = await self.preview_repo.get(preview_id)
        if not preview:
            raise ValueError("Hairstyle preview not found")

        cancelled_preview = await self.preview_repo.update(
            preview_id,
            {
                "status": HairstylePreviewStatus.CANCELLED,
                "error": None,
            },
        )
        return await self._refresh_preview_asset_urls(cancelled_preview)
