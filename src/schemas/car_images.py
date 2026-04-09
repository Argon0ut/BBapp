from pydantic import BaseModel
from enum import Enum
from src.models.car_images import CarImageType

class CarImageResponseSchema(BaseModel):
    id : int
    car_id : int
    image_type : CarImageType
    file_path : str

class CarImageAddressSchema(BaseModel):
    image_type : CarImageType
    file_path : str

class CarImageCompleteSchema(BaseModel):
    front : bool = False
    rear : bool = False
    left : bool = False
    right : bool = False

    partially_completed : bool = False
    complete : bool = False

#Upload schema != response schema
#Upload uses UploadFile, not pydantic


