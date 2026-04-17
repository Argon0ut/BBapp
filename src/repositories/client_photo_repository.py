from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client_photos import ClientPhoto
from src.utils.repository import AbstractRepository


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

    async def get_one(self, user_id: int):
        result = await self.session.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalars().all()

    async def delete_one(self, user_id: int):
        photos = await self.get_one(user_id)

        if not photos:
            return {"success": False}

        photo = photos[0]
        await self.session.delete(photo)
        await self.session.commit()
        return {"success": True}
