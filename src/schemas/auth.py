from datetime import datetime

from pydantic import BaseModel, Field

from src.models.auth import UserRole


class RegisterUserSchema(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.USER


class LoginSchema(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1)


class AuthUserResponseSchema(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class AuthSessionResponseSchema(BaseModel):
    session_token: str
    expires_at: datetime
    user: AuthUserResponseSchema


class MessageSchema(BaseModel):
    ok: bool
    message: str
