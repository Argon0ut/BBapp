from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db
from src.models.car_images import CarImage
from src.utils.repository import AbstractRepository


#Repository:
# DOES create entities
# DOES NOT touch FastAPI
# DOES NOT validate inputs


class CarsImageRepository(AbstractRepository):
    model = CarImage

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> CarImage:
        image = CarImage(**data)
        self.session.add(image)
        await self.session.commit()
        await self.session.refresh(image)
        return image


    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()


    async def get_one(self, car_id: int):
        result = await  self.session.execute(select(self.model).where(self.model.car_id == car_id))
        return result.scalar_one_or_none()


    async def delete_one(self, car_id : int):
        car = await self.get_one(car_id)

        if car is None:
            return {'success' : False}

        await self.session.delete(car)
        await self.session.commit()
        return {'success' : True}

