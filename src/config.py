import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    hf_api_key: str = os.getenv("HF_API_KEY", "")
    hf_secret_key: str = os.getenv("HF_SECRET_KEY", "")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    hf_image_model_id: str = os.getenv("HF_IMAGE_MODEL_ID", "higgsfield-ai/soul/standard")
    hf_timeout_seconds: float = float(os.getenv("HF_TIMEOUT_SECONDS", "30"))
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "session_token")
    cors_allowed_origins: list[str] = [
        origin.strip().rstrip("/")
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    @property
    def has_higgsfield_credentials(self) -> bool:
        return bool(self.hf_api_key and self.hf_secret_key)

    @property
    def authorization_header(self) -> str:
        return f"Key {self.hf_api_key}:{self.hf_secret_key}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
