import os

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from src.models.client_photos import ClientPhoto, ClientPhotoType
from src.repositories.client_photo_repository import ClientPhotosRepository
from src.services.image_storage_service import ImageStorageService

UPLOAD_DIR = "uploads/client_photos"
ALLOWED_TYPES = ["image/jpg", "image/png", "image/webp", "image/jpeg"]


class ClientPhotoService:
    def __init__(
        self,
        client_photos_repo: ClientPhotosRepository,
        image_storage_service: ImageStorageService,
    ):
        self.client_photos_repo = client_photos_repo
        self.image_storage_service = image_storage_service

    async def _serialize_photo(self, photo: ClientPhoto) -> dict:
        file_name = self.image_storage_service.extract_file_name(photo.file_name)
        if self.image_storage_service.enabled:
            lookup_key = self.image_storage_service.build_client_photo_key(
                user_id=photo.user_id,
                file_name=file_name,
            )
        else:
            lookup_key = os.path.join(UPLOAD_DIR, file_name)
        file_url = await self.image_storage_service.get_client_photo_url(lookup_key)
        return {
            "id": photo.id,
            "user_id": photo.user_id,
            "photo_type": ClientPhotoType(photo.photo_type),
            "file_name": file_name,
            "file_url": file_url,
        }

    async def add_photo(
        self,
        user_id: int,
        photo_type: ClientPhotoType,
        file: UploadFile,
    ) -> dict:
        if file.content_type not in ALLOWED_TYPES:
            raise ValueError("File type not allowed")

        extension = (file.filename or "image.jpg").rsplit(".", 1)[-1].lower()
        if extension not in {"jpg", "jpeg", "png", "webp"}:
            extension = "jpg"
        content_type = file.content_type or "image/jpeg"

        try:
            content = await file.read()
            await file.seek(0)
        except OSError as exc:
            raise RuntimeError(f"Unable to read uploaded file: {exc}") from exc

        try:
            if self.image_storage_service.enabled:
                file_name = await self.image_storage_service.upload_client_photo(
                    user_id=user_id,
                    photo_type=photo_type.value,
                    extension=extension,
                    content=content,
                    content_type=content_type,
                )
            else:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                file_name = f"{photo_type.value}_{user_id}.{extension}"
                local_path = os.path.join(UPLOAD_DIR, file_name)
                with open(local_path, "wb") as f:
                    f.write(content)
        except OSError as exc:
            raise RuntimeError(f"Unable to save uploaded file: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unable to upload file: {exc}") from exc

        try:
            existing = await self.client_photos_repo.get_by_user_and_type(
                user_id, photo_type.value
            )
            if existing:
                updated = await self.client_photos_repo.update_one(
                    existing.id,
                    {
                        "file_name": file_name,
                    },
                )
                return await self._serialize_photo(updated)

            data = {
                "user_id": user_id,
                "photo_type": photo_type.value,
                "file_name": file_name,
            }
            created = await self.client_photos_repo.add_one(data)
            return await self._serialize_photo(created)
        except SQLAlchemyError as exc:
            # Helps expose schema mismatch issues (e.g. DB not migrated to user_id).
            raise RuntimeError(f"Database error while saving photo: {exc}") from exc

    async def get_photos_by_user(self, user_id: int):
        photos = await self.client_photos_repo.get_one(user_id)
        res = []
        for photo in photos:
            file_name = self.image_storage_service.extract_file_name(photo.file_name)
            if self.image_storage_service.enabled:
                lookup_key = self.image_storage_service.build_client_photo_key(
                    user_id=photo.user_id,
                    file_name=file_name,
                )
            else:
                lookup_key = os.path.join(UPLOAD_DIR, file_name)
            file_url = await self.image_storage_service.get_client_photo_url(lookup_key)
            res.append(
                {
                    "photo_type": ClientPhotoType(photo.photo_type),
                    "file_name": file_name,
                    "file_url": file_url,
                }
            )
        return res

    async def get_status(self, user_id: int):
        photos = await self.client_photos_repo.get_one(user_id)
        present = set()
        for photo in photos:
            present.add(ClientPhotoType(photo.photo_type))

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
