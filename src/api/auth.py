from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from src.api.dependencies import auth_service as auth_service_dependency
from src.api.dependencies import get_current_user, get_session_token
from src.config import get_settings
from src.models.auth import AuthUser
from src.schemas.auth import (
    AuthSessionResponseSchema,
    AuthUserResponseSchema,
    LoginSchema,
    MessageSchema,
    RegisterUserSchema,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthUserResponseSchema, status_code=201)
async def register(
    payload: RegisterUserSchema,
    service: Annotated[AuthService, Depends(auth_service_dependency)],
):
    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/login", response_model=AuthSessionResponseSchema)
async def login(
    payload: LoginSchema,
    response: Response,
    service: Annotated[AuthService, Depends(auth_service_dependency)],
):
    try:
        user, session_token, expires_at = await service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )

    return {
        "session_token": session_token,
        "expires_at": expires_at,
        "user": user,
    }


@router.post("/logout", response_model=MessageSchema)
async def logout(
    response: Response,
    session_token: Annotated[str, Depends(get_session_token)],
    service: Annotated[AuthService, Depends(auth_service_dependency)],
):
    settings = get_settings()
    await service.logout(session_token)
    response.delete_cookie(settings.session_cookie_name)
    return {"ok": True, "message": "Logged out"}


@router.get("/me", response_model=AuthUserResponseSchema)
async def me(current_user: Annotated[AuthUser, Depends(get_current_user)]):
    return current_user
