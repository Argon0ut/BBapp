from typing import Annotated, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from src.api.dependencies import client_photo_service as client_photo_dependency
from src.schemas.client_photos import (
    ClientPhotoResponseSchema,
    ClientPhotoAddressSchema,
    ClientPhotoCompletenessSchema,
)
from src.services.client_photo_service import ClientPhotoService
from src.models.client_photos import ClientPhotoType


router = APIRouter(
    prefix="/clients/{client_id}/photos",
    tags=["Client Photos"],
)


@router.post("", response_model=ClientPhotoResponseSchema, status_code=201)
async def upload_client_photo(
        client_id: int,
        photo_type: ClientPhotoType,
        client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
        file: UploadFile = File(...),
):
    return await client_photo_service.add_photo(client_id, photo_type, file)


@router.get('', response_model=List[ClientPhotoAddressSchema], status_code=200)
async def get_client_photos(
    client_id: int,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
):
    try:
        return await client_photo_service.get_photos_by_client(client_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get('/status', status_code=200, response_model=ClientPhotoCompletenessSchema)
async def get_photo_completeness_status(
    client_id: int,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
):
    return await client_photo_service.get_status(client_id)
