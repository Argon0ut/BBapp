from pydantic import BaseModel
from typing import Optional


class ClientSchema(BaseModel):
    id: int
    brand: str
    model: str
    year: int

    model_config = {
        'from_attributes': True
    }


class ClientCreateSchema(BaseModel):
    brand: str
    model: str
    year: int


class ClientUpdateSchema(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


class ClientPutSchema(BaseModel):
    brand: str
    model: str
    year: int


class ClientResponseSchema(BaseModel):
    id: int
    brand: str
    model: str
    year: int

    model_config = {
        'from_attributes': True
    }
