from fastapi import FastAPI
from src.api.clients import client_router
from src.api.client_photos import router as client_photos_router
from src.api.hairstyle_previews import router as hairstyle_previews_router

app = FastAPI()
app.include_router(client_router)
app.include_router(client_photos_router)
app.include_router(hairstyle_previews_router)
