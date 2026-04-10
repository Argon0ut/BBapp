from fastapi import APIRouter, Depends, HTTPException

from src.schemas.clients import ClientCreateSchema, ClientUpdateSchema, ClientResponseSchema

from typing import Annotated, List

from src.services.client_service import ClientsService
from src.api.dependencies import clients_service as clients_service_dependency

client_router = APIRouter(
    prefix='/clients',
    tags=['Clients'],
)

@client_router.post('/create', response_model=ClientResponseSchema, status_code=201)
async def create_client(
    client: ClientCreateSchema,
    clients_service: Annotated[ClientsService, Depends(clients_service_dependency)],
):
    return await clients_service.add_client(client)


@client_router.get('', response_model=List[ClientResponseSchema])
async def get_all_clients(
    clients_service: Annotated[ClientsService, Depends(clients_service_dependency)],
):
    return await clients_service.get_all_clients()


@client_router.get('/{client_id}', response_model=ClientResponseSchema)
async def get_client(
    client_id: int,
    clients_service: Annotated[ClientsService, Depends(clients_service_dependency)],
):
    try:
        return await clients_service.get_client(client_id)
    except ValueError:
        raise HTTPException(status_code=404, detail='Client not found')


@client_router.patch('/{client_id}', response_model=ClientResponseSchema)
async def update_client(
    client_id: int,
    data: ClientUpdateSchema,
    clients_service: Annotated[ClientsService, Depends(clients_service_dependency)],
):
    try:
        return await clients_service.update_client(client_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail='Client not found')


@client_router.delete('/{client_id}', status_code=204)
async def delete_client(
    client_id: int,
    clients_service: Annotated[ClientsService, Depends(clients_service_dependency)],
):
    return await clients_service.delete_client(client_id)
