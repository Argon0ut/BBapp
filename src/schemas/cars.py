from uuid import UUID

from pydantic import BaseModel
from typing import Optional


class CarSchema(BaseModel):
    id : int
    brand: str
    model: str
    year: int

    model_config = {
        'from_attributes': True
    }


class CarAddSchema(BaseModel):
    brand: str
    model: str
    year: int


class CarUpdateSchema(BaseModel): # PATCH based schema
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


class CarPutSchema(BaseModel):
    brand: str
    model: str
    year: int


class CarResponseSchema(BaseModel):
    id: UUID
    brand: str
    model: str
    year: int