from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db
from src.models.clients import Client
from src.utils.repository import AbstractRepository

class ClientsRepository(AbstractRepository):
    model = Client

    def __init__(self, session: AsyncSession):
        self.session = session


    async def add_one(self, data:dict):
        client = Client(**data)
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client


    async def get_all(self):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()


    async def get_one(self, client_id: int):
        result = await self.session.execute(select(self.model).where(self.model.id == client_id))
        return result.scalar_one_or_none()


    async def update_one(self, client_id: int, updated_client_info: dict):
        client = await self.get_one(client_id)
        if client is None:
            return None

        for field, value in updated_client_info.items():
            setattr(client, field, value)

        await self.session.commit()
        await self.session.refresh(client)
        return client


    async def delete_one(self, client_id: int):
        client = await self.get_one(client_id)

        if client is None:
            return {'success': False}

        await self.session.delete(client)
        await self.session.commit()
        return {'success': True}
