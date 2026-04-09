from typing import Annotated, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from src.api.dependencies import car_image_service as car_image_dependency
from src.schemas.car_images import CarImageResponseSchema, CarImageAddressSchema, CarImageCompleteSchema
from src.services.car_image_service import CarImageService
from src.models.car_images import CarImageType


router = APIRouter(
    prefix="/cars/{car_id}/images",
    tags=["Car Images"],
)


@router.post("", response_model = CarImageResponseSchema, status_code = 201)
async def upload_car_image(
        car_id : int,
        image_type : CarImageType,
        cars_image_service: Annotated[CarImageService, Depends(car_image_dependency)],
        file : UploadFile = File(...),
):
    return await cars_image_service.add_image(car_id, image_type, file)


@router.get('', response_model = List[CarImageAddressSchema], status_code = 200)
async def get_car_images(car_id : int, cars_image_service : Annotated[CarImageService, Depends(car_image_dependency)]):
    try:
        return await cars_image_service.get_images_by_car(car_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get('/status', status_code = 200, response_model = CarImageCompleteSchema)
async def get_completeness_status(car_id : int, cars_image_service : Annotated[CarImageService, Depends(car_image_dependency)]):
    return await cars_image_service.get_status(car_id)
