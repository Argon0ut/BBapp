from datetime import datetime, timezone

from src.config import Settings
from src.models.hairstyle_preview_request import HairstylePreviewStatus
from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.client_photo_service import ClientPhotoService
from src.services.higgsfield_client import HiggsfieldClient
from src.services.image_storage_service import ImageStorageService


class HairstylePreviewService:
    def __init__(
        self,
        repo: HairstylePreviewRepository,
        client_photo_service: ClientPhotoService,
        higgsfield_client: HiggsfieldClient,
        image_storage_service: ImageStorageService,
        settings: Settings,
    ):
        self.preview_repo = repo
        self.client_photo_service = client_photo_service
        self.higgsfield_client = higgsfield_client
        self.image_storage_service = image_storage_service
        self.settings = settings

    def _build_webhook_url(self) -> str | None:
        if not self.settings.public_base_url:
            return None
        return f"{self.settings.public_base_url}/hairstyle-previews/webhooks/higgsfield-image"

    def _map_provider_status(self, provider_status: str | None) -> HairstylePreviewStatus:
        normalized = str(provider_status or "").lower()
        if normalized in {"queued", "pending"}:
            return HairstylePreviewStatus.QUEUED
        if normalized in {"processing", "running", "in_progress"}:
            return HairstylePreviewStatus.PROCESSING
        if normalized == "completed":
            return HairstylePreviewStatus.COMPLETED
        if normalized == "failed":
            return HairstylePreviewStatus.FAILED
        if normalized == "nsfw":
            return HairstylePreviewStatus.BLOCKED
        if normalized == "cancelled":
            return HairstylePreviewStatus.CANCELLED
        return HairstylePreviewStatus.QUEUED

    @staticmethod
    def _is_terminal_status(status: HairstylePreviewStatus) -> bool:
        return status in {
            HairstylePreviewStatus.COMPLETED,
            HairstylePreviewStatus.FAILED,
            HairstylePreviewStatus.BLOCKED,
            HairstylePreviewStatus.APPROVED,
            HairstylePreviewStatus.CANCELLED,
        }

    @staticmethod
    def _extract_image_url(payload: dict) -> str | None:
        images = payload.get("images") or []
        if images and isinstance(images[0], dict):
            image_url = images[0].get("url")
            if image_url:
                return image_url

        payload_data = payload.get("payload") or {}
        legacy_images = payload_data.get("images") or []
        if legacy_images and isinstance(legacy_images[0], dict):
            return legacy_images[0].get("url")

        return None

    async def _build_updates_from_provider_payload(self, preview: dict, payload: dict) -> dict:
        status = str(payload.get("status", "")).lower()
        updates: dict = {
            "status": self._map_provider_status(status),
            "error": None,
        }

        if payload.get("request_id"):
            updates["provider_request_id"] = payload["request_id"]
        if payload.get("status_url"):
            updates["status_url"] = payload["status_url"]
        if payload.get("cancel_url"):
            updates["cancel_url"] = payload["cancel_url"]

        if status == "completed":
            image_url = self._extract_image_url(payload)

            if image_url:
                try:
                    image_url = await self.image_storage_service.mirror_generated_image(
                        preview_id=preview["id"],
                        source_url=image_url,
                    )
                except Exception:
                    # Fall back to provider URL to avoid losing completion signal.
                    pass

            updates["generated_image_url"] = image_url
        elif status == "failed":
            updates["error"] = payload.get("error") or "Generation failed"
            updates["generated_image_url"] = None
        elif status == "nsfw":
            updates["error"] = "Blocked as NSFW"
            updates["generated_image_url"] = None
        elif status == "cancelled":
            updates["generated_image_url"] = None

        return updates

    async def create_preview(
        self,
        user_id: int,
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "720p",
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
            "status": HairstylePreviewStatus.QUEUED,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
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
        await self.preview_repo.add(request)

        try:
            provider_response = await self.higgsfield_client.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                webhook_url=self._build_webhook_url(),
            )
        except Exception as exc:
            return await self.preview_repo.update(
                preview_id,
                {
                    "status": HairstylePreviewStatus.FAILED,
                    "error": str(exc),
                },
            )

        return await self.preview_repo.update(
            preview_id,
            {
                "status": self._map_provider_status(provider_response["status"]),
                "provider_request_id": provider_response["request_id"],
                "status_url": provider_response["status_url"],
                "cancel_url": provider_response["cancel_url"],
                "error": None,
            },
        )

    async def get_preview(self, preview_id: int) -> dict | None:
        preview = await self.preview_repo.get(preview_id)
        if not preview:
            return None

        status_url = preview.get("status_url")
        if (
            not self._is_terminal_status(preview["status"])
            and status_url
            and self.settings.has_higgsfield_credentials
        ):
            try:
                provider_payload = await self.higgsfield_client.get_request_status(status_url)
                updates = await self._build_updates_from_provider_payload(preview, provider_payload)
                refreshed_preview = await self.preview_repo.update(preview_id, updates)
                if refreshed_preview:
                    return refreshed_preview
            except Exception:
                pass

        return preview

    async def approve_preview(self, preview_id: int):
        preview = await self.get_preview(preview_id)
        if not preview:
            raise ValueError("Hairstyle preview not found")
        if not preview.get("generated_image_url"):
            raise ValueError("Preview image is not ready yet")

        return await self.preview_repo.update(
            preview_id,
            {
                "status": HairstylePreviewStatus.APPROVED,
                "approved_image_url": preview["generated_image_url"],
                "error": None,
            },
        )

    async def regenerate_preview(
        self,
        preview_id: int,
        text_prompt: str | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
    ):
        preview = await self.get_preview(preview_id)
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
                "status": HairstylePreviewStatus.QUEUED,
                "generation_count": preview["generation_count"] + 1,
                "generated_image_url": None,
                "approved_image_url": None,
                "provider_request_id": None,
                "status_url": None,
                "cancel_url": None,
                "error": None,
            },
        )

        try:
            provider_response = await self.higgsfield_client.generate_image(
                prompt=next_prompt,
                aspect_ratio=next_aspect_ratio,
                resolution=next_resolution,
                webhook_url=self._build_webhook_url(),
            )
        except Exception as exc:
            return await self.preview_repo.update(
                preview_id,
                {
                    "status": HairstylePreviewStatus.FAILED,
                    "error": str(exc),
                },
            )

        return await self.preview_repo.update(
            preview_id,
            {
                "status": self._map_provider_status(provider_response["status"]),
                "provider_request_id": provider_response["request_id"],
                "status_url": provider_response["status_url"],
                "cancel_url": provider_response["cancel_url"],
                "error": None,
            },
        )

    async def cancel_preview(self, preview_id: int):
        preview = await self.get_preview(preview_id)
        if not preview:
            raise ValueError("Hairstyle preview not found")

        cancel_url = preview.get("cancel_url")
        if cancel_url and self.settings.has_higgsfield_credentials:
            try:
                await self.higgsfield_client.cancel_image(cancel_url)
            except Exception:
                pass

        return await self.preview_repo.update(
            preview_id,
            {
                "status": HairstylePreviewStatus.CANCELLED,
                "error": None,
            },
        )

    async def handle_higgsfield_webhook(self, payload: dict):
        provider_request_id = payload.get("request_id")
        if not provider_request_id:
            return {"ok": True, "ignored": True, "reason": "missing_request_id"}

        preview = await self.preview_repo.get_by_provider_request_id(provider_request_id)
        if not preview:
            return {"ok": True, "ignored": True, "reason": "unknown_request_id"}

        updates = await self._build_updates_from_provider_payload(preview, payload)
        await self.preview_repo.update(preview["id"], updates)
        return {"ok": True}
