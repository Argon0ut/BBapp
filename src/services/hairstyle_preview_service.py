from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.models.hairstyle_preview_request import HairstylePreviewRequest
from src.services.client_photo_service import ClientPhotoService
from src.services.ai_mock import run_mock_ai
from src.utils.repository import PlainRepository


class HairstylePreviewService(PlainRepository):
    def __init__(
            self,
            repo: HairstylePreviewRepository,
            client_photo_service: ClientPhotoService
    ):
        self.preview_repo = repo
        self.client_photo_service = client_photo_service


    async def create_preview(self, client_id: int, prompt: str):
        status = await self.client_photo_service.get_status(client_id)

        if not status['partially_completed']: #and not status['complete']:
            raise Exception("Client photos are not ready to be loaded to AI")

        preview_id = await self.preview_repo._next_id()
        photos = await self.client_photo_service.get_photos_by_client(client_id)
        ai_result_images = run_mock_ai(photos, preview_id) or []

        request = HairstylePreviewRequest(
            id=preview_id,
            client_id=client_id,
            text_prompt=prompt,
            # status = status,
            result_images=ai_result_images,
        )
        return await self.preview_repo.add(client_id, request)


    async def get_preview(self, preview_id: int) -> HairstylePreviewRequest:
        return await self.preview_repo.get(preview_id)

