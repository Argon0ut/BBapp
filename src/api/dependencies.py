from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.db import get_db_session
from src.models.auth import AuthUser, UserRole
from src.repositories.auth_repository import AuthRepository
from src.services.auth_service import AuthService
from src.services.user_service import UserService

from src.repositories.client_photo_repository import ClientPhotosRepository
from src.services.client_photo_service import ClientPhotoService
from src.services.image_storage_service import ImageStorageService

from src.repositories.hairstyle_preview_repository import HairstylePreviewRepository
from src.services.hairstyle_preview_service import HairstylePreviewService
from src.services.higgsfield_client import HiggsfieldClient


async def auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    repo = AuthRepository(session)
    settings = get_settings()
    return AuthService(repo, settings)


async def get_session_token(
    request: Request,
    x_session_token: Annotated[str | None, Header(alias="X-Session-Token")] = None,
) -> str:
    settings = get_settings()
    session_token = x_session_token or request.cookies.get(settings.session_cookie_name)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


async def get_current_user(
    session_token: Annotated[str, Depends(get_session_token)],
    auth: Annotated[AuthService, Depends(auth_service)],
) -> AuthUser:
    user = await auth.get_user_by_session_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def require_roles(*roles: UserRole):
    async def role_checker(
        current_user: Annotated[AuthUser, Depends(get_current_user)],
    ) -> AuthUser:
        if current_user.role not in {role.value for role in roles}:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker


def require_admin():
    return require_roles(UserRole.ADMIN)


async def user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserService:
    auth_repo = AuthRepository(session)
    return UserService(auth_repo)

async def client_photo_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ClientPhotoService:
    repo = ClientPhotosRepository(session)
    settings = get_settings()
    image_storage = ImageStorageService(settings)
    return ClientPhotoService(repo, image_storage)

async def hairstyle_preview_service(
    photo_service: Annotated[ClientPhotoService, Depends(client_photo_service)],
) -> HairstylePreviewService:
    repo = HairstylePreviewRepository()
    settings = get_settings()
    higgsfield_client = HiggsfieldClient(settings)
    image_storage = ImageStorageService(settings)
    return HairstylePreviewService(
        repo,
        photo_service,
        higgsfield_client,
        image_storage,
        settings,
    )
