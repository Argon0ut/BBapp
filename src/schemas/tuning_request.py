from pydantic import BaseModel
from typing import List
from src.models.tuning_request import TuningStatus

class TuningPromptSchema(BaseModel):
    text_prompt: str

class TuningRequestSchema(BaseModel):
    id : int
    car_id : int
    text_prompt : str
    result_images : List[str or None] #addresses of the images that were generated
    # status : TuningStatus
