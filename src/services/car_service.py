from src.models.cars import Car
from src.schemas.cars import CarAddSchema, CarUpdateSchema
from src.repositories.car_repository import CarsRepository
from src.db import db

class CarsService:
    def __init__(self, cars_repo : CarsRepository):
        self.cars_repo = cars_repo


    async def add_car(self, car_schema : CarAddSchema):
        cars_dict = car_schema.model_dump()
        return await self.cars_repo.add_one(cars_dict)


    async def get_all_cars(self):
        return await self.cars_repo.get_all()


    async def get_car(self, car_id : int):
        car_info = await self.cars_repo.get_one(car_id)
        if not car_info:
            raise ValueError('Car not found')
        return car_info


    async def update_car(self, car_id: int, car_info : CarUpdateSchema):
        updated_car_info = car_info.model_dump(exclude_unset=True) # the Optional fields that are unset are just excluded
        car = await self.cars_repo.update_one(car_id, updated_car_info)
        if not car:
            raise ValueError('Car not found')
        return car

    async def delete_car(self, car_id : int):
        return await self.cars_repo.delete_one(car_id)