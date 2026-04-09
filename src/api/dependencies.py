from src.repositories.car_repository import CarsRepository
from src.services.car_service import CarsService

from src.repositories.car_image_repository import CarsImageRepository
from src.services.car_image_service import CarImageService

from src.repositories.tuning_repository import TuningRepository
from src.services.tuning_service import TuningService


def cars_service() -> CarsService:
    repo = CarsRepository()
    return CarsService(repo)

def car_image_service() -> CarImageService:
    repo = CarsImageRepository()
    return CarImageService(repo)

def tuning_service() -> TuningService:
    repo = TuningRepository()
    images_service = car_image_service()
    return TuningService(repo, images_service)