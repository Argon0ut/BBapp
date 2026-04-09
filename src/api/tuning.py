from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import tuning_service as tuning_dependency
from src.services.tuning_service import TuningService
from src.schemas.tuning_request import TuningRequestSchema, TuningPromptSchema

router = APIRouter()


@router.post("/tuning", tags=["Tuning"], response_model = TuningRequestSchema)
async def create_tuning(
        car_id : int,
        data : TuningPromptSchema,
        service : Annotated[TuningService, Depends(tuning_dependency)]
):
    try:
        print("trying")
        return await service.create_tuning(car_id, data.text_prompt)
    except Exception as e:
        print('errrorrrr')
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tuning_id}/", tags=["Tuning"])#, response_model = TuningRequestSchema)
async def get_tuning(
        tuning_id : int,
        service : Annotated[TuningService, Depends(tuning_dependency)]
):
    tuning = await service.get_tuning(tuning_id)
    if not tuning:
        raise HTTPException(status_code=404, detail="Tuning not found")
    return tuning

