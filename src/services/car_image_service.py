import os #needed to work with the directory paths
from fastapi import UploadFile

from src.repositories.car_image_repository import CarsImageRepository
from src.models.car_images import CarImage, CarImageType
from src.schemas.car_images import CarImageCompleteSchema

UPLOAD_DIR = 'uploads/cars'
ALLOWED_TYPES = ['image/jpg', 'image/png', 'image/webp', 'image/jpeg']


class CarImageService:

    def __init__(self, car_images_repo : CarsImageRepository):
        self.car_images_repo = car_images_repo

    async def add_image(
            self,
            car_id : int,
            image_type : CarImageType,
            file : UploadFile
    ) -> CarImage:

        if file.content_type not in ALLOWED_TYPES:
            raise Exception('File Type not allowed')

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"car_{car_id}_{image_type}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, 'wb') as f:
            while content := await file.read(1024 * 1024):
                f.write(content)

        data = {
            car_id : car_id,
            image_type : image_type,
            file_path : file_path
        }
        return await self.car_images_repo.add_one(data)


    async def get_images_by_car(self, car_id : int):
        images = await self.car_images_repo.get_one(car_id)
        res = []
        for image in images:
            res.append({
                'image_type' : image.image_type,
                'file_path' : image.file_path,
            })
        return res


    async def get_status(self, car_id : int):
        images = await self.get_images_by_car(car_id)
        present = set()
        for image in images:
            present.add(image['image_type'])

        front = CarImageType.FRONT in present
        rear = CarImageType.REAR in present
        left = CarImageType.LEFT in present
        right = CarImageType.RIGHT in present

        partially_complete = front and rear
        fully_complete = front and rear and left and right

        return {
            'front' : front,
            'rear' : rear,
            'left' : left,
            'right' : right,
            'partially_completed' : partially_complete,
            'complete' : fully_complete
        }
