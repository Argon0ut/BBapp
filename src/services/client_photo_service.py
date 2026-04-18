import os

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from src.models.client_photos import ClientPhoto, ClientPhotoType
from src.repositories.client_photo_repository import ClientPhotosRepository

UPLOAD_DIR = "uploads/client_photos"
ALLOWED_TYPES = ["image/jpg", "image/png", "image/webp", "image/jpeg"]


class ClientPhotoService:
    def __init__(self, client_photos_repo: ClientPhotosRepository):
        self.client_photos_repo = client_photos_repo

    async def add_photo(
        self,
        user_id: int,
        photo_type: ClientPhotoType,
        file: UploadFile,
    ) -> ClientPhoto:
        if file.content_type not in ALLOWED_TYPES:
            raise ValueError("File type not allowed")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        extension = (file.filename or "image.jpg").rsplit(".", 1)[-1].lower()
        if extension not in {"jpg", "jpeg", "png", "webp"}:
            extension = "jpg"
        filename = f"user_{user_id}_{photo_type.value}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(file_path, "wb") as f:
                while content := await file.read(1024 * 1024):
                    f.write(content)
        except OSError as exc:
            raise RuntimeError(f"Unable to save uploaded file: {exc}") from exc

        try:
            existing = await self.client_photos_repo.get_by_user_and_type(
                user_id, photo_type.value
            )
            if existing:
                updated = await self.client_photos_repo.update_one(
                    existing.id,
                    {
                        "file_path": file_path,
                    },
                )
                return updated

            data = {
                "user_id": user_id,
                "photo_type": photo_type.value,
                "file_path": file_path,
            }
            return await self.client_photos_repo.add_one(data)
        except SQLAlchemyError as exc:
            # Helps expose schema mismatch issues (e.g. DB not migrated to user_id).
            raise RuntimeError(f"Database error while saving photo: {exc}") from exc

    async def get_photos_by_user(self, user_id: int):
        photos = await self.client_photos_repo.get_one(user_id)
        res = []
        for photo in photos:
            res.append(
                {
                    "photo_type": ClientPhotoType(photo.photo_type),
                    "file_path": photo.file_path,
                }
            )
        return res

    async def get_status(self, user_id: int):
        photos = await self.get_photos_by_user(user_id)
        present = set()
        for photo in photos:
            present.add(ClientPhotoType(photo["photo_type"]))

        front = ClientPhotoType.FRONT in present
        rear = ClientPhotoType.REAR in present
        left = ClientPhotoType.LEFT in present
        right = ClientPhotoType.RIGHT in present

        partially_complete = bool(present)
        fully_complete = front and rear and left and right

        return {
            "front": front,
            "rear": rear,
            "left": left,
            "right": right,
            "partially_completed": partially_complete,
            "complete": fully_complete,
        }
