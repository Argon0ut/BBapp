from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db
from src.models.client_photos import ClientPhoto
from src.utils.repository import AbstractRepository


#Repository:
# DOES create entities
# DOES NOT touch FastAPI
# DOES NOT validate inputs


class ClientPhotosRepository(AbstractRepository):
    model = ClientPhoto

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict) -> ClientPhoto:
        photo = ClientPhoto(**data)
        self.session.add(photo)
        await self.session.commit()
        await self.session.refresh(photo)
        return photo


    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()


    async def get_one(self, client_id: int):
        result = await self.session.execute(select(self.model).where(self.model.client_id == client_id))
        return result.scalars().all()


    async def delete_one(self, client_id: int):
        photos = await self.get_one(client_id)

        if not photos:
            return {'success' : False}

        photo = photos[0]
        await self.session.delete(photo)
        await self.session.commit()
        return {'success' : True}
