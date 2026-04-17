from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.api.dependencies import (
    client_photo_service as client_photo_dependency,
    get_current_user,
)
from src.models.auth import AuthUser
from src.models.client_photos import ClientPhotoType
from src.schemas.client_photos import (
    ClientPhotoAddressSchema,
    ClientPhotoCompletenessSchema,
    ClientPhotoResponseSchema,
)
from src.services.client_photo_service import ClientPhotoService

router = APIRouter(
    prefix="/users/me/photos",
    tags=["User Photos"],
)


@router.post("", response_model=ClientPhotoResponseSchema, status_code=201)
async def upload_user_photo(
    photo_type: ClientPhotoType,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    return await client_photo_service.add_photo(current_user.id, photo_type, file)


@router.get("", response_model=List[ClientPhotoAddressSchema], status_code=200)
async def get_user_photos(
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    try:
        return await client_photo_service.get_photos_by_user(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", status_code=200, response_model=ClientPhotoCompletenessSchema)
async def get_photo_completeness_status(
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    return await client_photo_service.get_status(current_user.id)
