from src.schemas.clients import ClientCreateSchema, ClientUpdateSchema
from src.repositories.client_repository import ClientsRepository
from src.db import db

class ClientsService:
    def __init__(self, clients_repo: ClientsRepository):
        self.clients_repo = clients_repo


    async def add_client(self, client_schema: ClientCreateSchema):
        client_data = client_schema.model_dump()
        return await self.clients_repo.add_one(client_data)


    async def get_all_clients(self):
        return await self.clients_repo.get_all()


    async def get_client(self, client_id: int):
        client_info = await self.clients_repo.get_one(client_id)
        if not client_info:
            raise ValueError('Client not found')
        return client_info


    async def update_client(self, client_id: int, client_info: ClientUpdateSchema):
        updated_client_info = client_info.model_dump(exclude_unset=True)
        client = await self.clients_repo.update_one(client_id, updated_client_info)
        if not client:
            raise ValueError('Client not found')
        return client

    async def delete_client(self, client_id: int):
        return await self.clients_repo.delete_one(client_id)
