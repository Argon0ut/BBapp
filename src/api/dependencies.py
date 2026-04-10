from src.repositories.client_repository import ClientsRepository
from src.services.client_service import ClientsService

from src.repositories.client_photo_repository import ClientPhotosRepository
from src.services.client_photo_service import ClientPhotoService

from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.hairstyle_preview_service import HairstylePreviewService


def clients_service() -> ClientsService:
    repo = ClientsRepository()
    return ClientsService(repo)

def client_photo_service() -> ClientPhotoService:
    repo = ClientPhotosRepository()
    return ClientPhotoService(repo)

def hairstyle_preview_service() -> HairstylePreviewService:
    repo = HairstylePreviewRepository()
    photos_service = client_photo_service()
    return HairstylePreviewService(repo, photos_service)
