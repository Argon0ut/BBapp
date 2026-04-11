import os #needed to work with the directory paths
from fastapi import UploadFile

from src.repositories.client_photo_repository import ClientPhotosRepository
from src.models.client_photos import ClientPhoto, ClientPhotoType
UPLOAD_DIR = 'uploads/client_photos'
ALLOWED_TYPES = ['image/jpg', 'image/png', 'image/webp', 'image/jpeg']


class ClientPhotoService:

    def __init__(self, client_photos_repo: ClientPhotosRepository):
        self.client_photos_repo = client_photos_repo

    async def add_photo(
            self,
            client_id: int,
            photo_type: ClientPhotoType,
            file: UploadFile
    ) -> ClientPhoto:

        if file.content_type not in ALLOWED_TYPES:
            raise Exception('File Type not allowed')

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"client_{client_id}_{photo_type.value}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, 'wb') as f:
            while content := await file.read(1024 * 1024):
                f.write(content)

        data = {
            'client_id': client_id,
            'photo_type': photo_type,
            'file_path': file_path,
        }
        return await self.client_photos_repo.add_one(data)


    async def get_photos_by_client(self, client_id: int):
        photos = await self.client_photos_repo.get_one(client_id)
        res = []
        for photo in photos:
            res.append({
                'photo_type': photo.photo_type,
                'file_path': photo.file_path,
            })
        return res


    async def get_status(self, client_id: int):
        photos = await self.get_photos_by_client(client_id)
        present = set()
        for photo in photos:
            present.add(photo['photo_type'])

        front = ClientPhotoType.FRONT in present
        rear = ClientPhotoType.REAR in present
        left = ClientPhotoType.LEFT in present
        right = ClientPhotoType.RIGHT in present

        partially_complete = bool(present)
        fully_complete = front and rear and left and right

        return {
            'front' : front,
            'rear' : rear,
            'left' : left,
            'right' : right,
            'partially_completed' : partially_complete,
            'complete' : fully_complete
        }
