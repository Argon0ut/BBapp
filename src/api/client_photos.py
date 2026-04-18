from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile

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

legacy_router = APIRouter(
    prefix="/clients/{user_id}/photos",
    tags=["User Photos"],
)


@router.post("/upload", response_model=ClientPhotoResponseSchema, status_code=201)
async def upload_user_photo(
    photo_type: ClientPhotoType,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    try:
        return await client_photo_service.add_photo(current_user.id, photo_type, file)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    


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


@router.get("/{photo_type}/file")
async def get_user_photo_file(
    photo_type: ClientPhotoType,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    try:
        content, content_type, file_name = await client_photo_service.get_photo_content(
            user_id=current_user.id,
            photo_type=photo_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )


@legacy_router.post("", response_model=ClientPhotoResponseSchema, status_code=201)
async def upload_legacy_user_photo(
    user_id: int,
    photo_type: ClientPhotoType,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Path user_id must match signed-in user")
    try:
        return await client_photo_service.add_photo(user_id, photo_type, file)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@legacy_router.get("", response_model=List[ClientPhotoAddressSchema], status_code=200)
async def get_legacy_user_photos(
    user_id: int,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Path user_id must match signed-in user")
    try:
        return await client_photo_service.get_photos_by_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@legacy_router.get("/status", status_code=200, response_model=ClientPhotoCompletenessSchema)
async def get_legacy_photo_completeness_status(
    user_id: int,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Path user_id must match signed-in user")
    return await client_photo_service.get_status(user_id)


@legacy_router.get("/{photo_type}/file")
async def get_legacy_user_photo_file(
    user_id: int,
    photo_type: ClientPhotoType,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Path user_id must match signed-in user")

    try:
        content, content_type, file_name = await client_photo_service.get_photo_content(
            user_id=user_id,
            photo_type=photo_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )


@legacy_router.get("/{photo_type}/provider-file")
async def get_provider_user_photo_file(
    user_id: int,
    photo_type: ClientPhotoType,
    expires_at: int,
    token: str,
    client_photo_service: Annotated[ClientPhotoService, Depends(client_photo_dependency)],
):
    if not client_photo_service.can_access_provider_file(
        user_id=user_id,
        photo_type=photo_type,
        expires_at=expires_at,
        token=token,
    ):
        raise HTTPException(status_code=403, detail="Invalid or expired media token")

    try:
        content, content_type, file_name = await client_photo_service.get_photo_content(
            user_id=user_id,
            photo_type=photo_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{file_name}"'},
    )
