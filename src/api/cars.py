from fastapi import APIRouter, Depends, HTTPException

from src.schemas.cars import CarAddSchema, CarUpdateSchema, CarResponseSchema

from typing import Annotated, List

from src.services.car_service import CarsService
from src.api.dependencies import cars_service as cars_service_dependency

car_router = APIRouter(
    prefix = '/cars',
    tags = ['Cars']
)

@car_router.post('/create', response_model=CarResponseSchema, status_code=201)
async def create_car(car: CarAddSchema, cars_service : Annotated[CarsService , Depends(cars_service_dependency)]):
    car_info = await cars_service.add_car(car)
    return car_info


@car_router.get('', response_model= List[CarResponseSchema])
async def get_all_cars(cars_service : Annotated[CarsService , Depends(cars_service_dependency)]):
    return await cars_service.get_all_cars()


@car_router.get('/{car_id}', response_model = CarResponseSchema)
async def get_car(car_id : int, cars_service : Annotated[CarsService , Depends(cars_service_dependency)]):
    try:
        car_info = await cars_service.get_car(car_id)
        return car_info
    except ValueError:
        raise HTTPException(status_code=404, detail='Car not found')


@car_router.patch('/{car_id}', response_model=CarResponseSchema)
async def update_car(car_id : int, data : CarUpdateSchema, cars_service : Annotated[CarsService , Depends(cars_service_dependency)]):
    try:
        return await cars_service.update_car(car_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail='Car not found')


@car_router.delete('/{car_id}', status_code=204)
async def delete_car(car_id : int, cars_service : Annotated[CarsService , Depends(cars_service_dependency)]):
    return await cars_service.delete_car(car_id)