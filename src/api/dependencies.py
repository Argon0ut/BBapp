from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.db import get_db_session
from src.repositories.client_repository import ClientsRepository
from src.services.client_service import ClientsService

from src.repositories.client_photo_repository import ClientPhotosRepository
from src.services.client_photo_service import ClientPhotoService

from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.hairstyle_preview_service import HairstylePreviewService
from src.services.higgsfield_client import HiggsfieldClient


async def clients_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ClientsService:
    repo = ClientsRepository(session)
    return ClientsService(repo)

async def client_photo_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ClientPhotoService:
    repo = ClientPhotosRepository(session)
    return ClientPhotoService(repo)

async def hairstyle_preview_service(
    photo_service: Annotated[ClientPhotoService, Depends(client_photo_service)],
) -> HairstylePreviewService:
    repo = HairstylePreviewRepository()
    settings = get_settings()
    higgsfield_client = HiggsfieldClient(settings)
    return HairstylePreviewService(repo, photo_service, higgsfield_client, settings)
