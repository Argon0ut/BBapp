from fastapi import FastAPI
from src.api.cars import car_router
from src.api.car_images import router as car_images_router
from src.api.tuning import router as tuning_router

app = FastAPI()
app.include_router(car_router)
app.include_router(car_images_router)
app.include_router(tuning_router)
