from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    get_current_user,
    require_roles,
    user_service as user_service_dependency,
)
from src.models.auth import AuthUser, UserRole
from src.schemas.clients import UserResponseSchema, UserUpdateSchema
from src.services.user_service import UserService

client_router = APIRouter(
    prefix="/clients",
    tags=["Users"],
)


@client_router.get("", response_model=List[UserResponseSchema])
async def get_all_users(
    user_service: Annotated[UserService, Depends(user_service_dependency)],
    current_user: Annotated[AuthUser, Depends(require_roles(UserRole.ADMIN))],
):
    return await user_service.get_all_users()


@client_router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(user_service_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        return await user_service.get_user(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")


@client_router.patch("/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: int,
    data: UserUpdateSchema,
    user_service: Annotated[UserService, Depends(user_service_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        return await user_service.update_user(user_id, data, current_user)
    except ValueError as exc:
        message = str(exc)
        if message == "User not found":
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)


@client_router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(user_service_dependency)],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    try:
        await user_service.delete_user(user_id, current_user)
    except ValueError as exc:
        message = str(exc)
        if message == "User not found":
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=403, detail=message)
