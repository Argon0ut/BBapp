from pydantic import BaseModel
from src.models.client_photos import ClientPhotoType

class ClientPhotoResponseSchema(BaseModel):
    id: int
    user_id: int
    photo_type: ClientPhotoType
    file_path: str

class ClientPhotoAddressSchema(BaseModel):
    photo_type: ClientPhotoType
    file_path: str

class ClientPhotoCompletenessSchema(BaseModel):
    front: bool = False
    rear: bool = False
    left: bool = False
    right: bool = False

    partially_completed: bool = False
    complete: bool = False

#Upload schema != response schema
#Upload uses UploadFile, not pydantic
