from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db
from src.models.cars import Car
from src.utils.repository import AbstractRepository

class CarsRepository(AbstractRepository):
    model = Car

    def __init__(self, session: AsyncSession):
        self.session = session


    async def add_one(self, data:dict):
        car = Car(**data)
        self.session.add(car)
        await self.session.commit()
        await self.session.refresh(car)
        return car


    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()


    async def get_one(self, car_id: int):
        result = await self.session.execute(select(self.model).where(self.model.id == car_id))
        return result.scalar_one_or_none()


    async def update_one(self, car_id : int, updated_car_info : dict):
        car = await self.get_one(car_id)
        if car is None:
            return None

        for field, value in updated_car_info.items():
            setattr(car, field, value)

        await self.session.commit()
        await self.session.refresh(car)
        return car


    async def delete_one(self, car_id: int):
        car = await self.get_one(car_id)

        if car is None:
            return {'success': False}

        await self.session.delete(car)
        await self.session.commit()
        return {'success': True}
