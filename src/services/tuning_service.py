from src.repositories.car_image_repository import CarsImageRepository
from src.repositories.tuning_repository import TuningRepository
from src.models.tuning_request import TuningRequest
from src.services.car_image_service import CarImageService
from src.services.ai_mock import run_mock_ai
from src.utils.repository import PlainRepository


class TuningService(PlainRepository):
    def __init__(
            self,
            repo: TuningRepository,
            car_image_service: CarImageService
    ):
        self.tuning_repo = repo
        self.car_image_service = car_image_service


    async def create_tuning(self, car_id : int, prompt : str):
        status = await self.car_image_service.get_status(car_id)

        if not status['partially_completed']: #and not status['complete']:
            raise Exception("Car images are not ready to be loaded to AI")

        tuning_id = await self.tuning_repo._next_id()
        images = await self.car_image_service.get_images_by_car(car_id)
        ai_result_images = run_mock_ai(images, tuning_id) or []

        request = TuningRequest(
            id = tuning_id,
            car_id = car_id,
            text_prompt = prompt,
            # status = status,
            result_images = ai_result_images
        )
        return await self.tuning_repo.add(car_id, request)


    async def get_tuning(self, tuning_id : int) -> TuningRequest:
        return await self.tuning_repo.get(tuning_id)


