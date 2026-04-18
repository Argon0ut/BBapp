from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.auth import router as auth_router
from src.api.clients import client_router
from src.api.client_photos import legacy_router as client_photos_legacy_router
from src.api.client_photos import router as client_photos_router
from src.api.hairstyle_previews import router as hairstyle_previews_router
from src.config import get_settings

app = FastAPI()
settings = get_settings()
Path("generated_images").mkdir(parents=True, exist_ok=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"ok": True, "message": "server is running"}


app.include_router(client_router)
app.include_router(client_photos_router)
app.include_router(client_photos_legacy_router)
app.include_router(hairstyle_previews_router)
app.include_router(auth_router)
app.mount("/generated-images", StaticFiles(directory="generated_images"), name="generated-images")
