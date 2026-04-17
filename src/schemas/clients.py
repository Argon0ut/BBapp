from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.models.auth import UserRole


class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponseSchema(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
