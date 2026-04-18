import os
from functools import lru_cache

from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseModel):
    hf_api_key: str = os.getenv("HF_API_KEY", "")
    hf_secret_key: str = os.getenv("HF_SECRET_KEY", "")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    hf_image_model_id: str = os.getenv("HF_IMAGE_MODEL_ID", "higgsfield-ai/soul/standard")
    hf_timeout_seconds: float = float(os.getenv("HF_TIMEOUT_SECONDS", "30"))
    hf_webhook_timeout_seconds: float = float(os.getenv("HF_WEBHOOK_TIMEOUT_SECONDS", "60"))
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "session_token")
    session_cookie_samesite: str = os.getenv("SESSION_COOKIE_SAMESITE", "none")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
    cors_allowed_origins: list[str] = [
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]
    aws_access_key: str = os.getenv("AWS_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY", ""))
    aws_secret_key: str = os.getenv("AWS_SECRET_KEY", os.getenv("AWS_SECRET_KEY", ""))
    aws_region: str = os.getenv("AWS_REGION", "")
    aws_bucket_name: str = os.getenv("AWS_BUCKET_NAME", "").strip().strip("\"'")
    aws_public_base_url: str = os.getenv("AWS_PUBLIC_BASE_URL", "").rstrip("/")
    s3_client_photo_prefix: str = os.getenv("S3_CLIENT_PHOTO_PREFIX", "client-photos").strip("/")
    s3_generated_photo_prefix: str = os.getenv("S3_GENERATED_PHOTO_PREFIX", "generated-images").strip("/")
    s3_presigned_ttl_seconds: int = int(os.getenv("S3_PRESIGNED_TTL_SECONDS", "3600"))

    @property
    def has_higgsfield_credentials(self) -> bool:
        return bool(self.hf_api_key and self.hf_secret_key)

    @property
    def has_s3_credentials(self) -> bool:
        return bool(
            self.aws_access_key
            and self.aws_secret_key
            and self.aws_region
            and self.aws_bucket_name
        )

    @property
    def authorization_header(self) -> str:
        return f"Key {self.hf_api_key}:{self.hf_secret_key}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
