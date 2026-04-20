import os
from functools import lru_cache

from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


def _getenv_stripped(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value.strip().strip("\"'")
    return ""


def _resolve_aws_credentials() -> tuple[str, str]:
    standard_access = _getenv_stripped("AWS_ACCESS_KEY_ID")
    standard_secret = _getenv_stripped("AWS_SECRET_ACCESS_KEY")
    legacy_access = _getenv_stripped("AWS_ACCESS_KEY")
    legacy_secret = _getenv_stripped("AWS_SECRET_KEY")

    standard_present = bool(standard_access or standard_secret)
    legacy_present = bool(legacy_access or legacy_secret)

    if standard_present and legacy_present:
        if standard_access and standard_secret and legacy_access and legacy_secret:
            if standard_access != legacy_access or standard_secret != legacy_secret:
                raise ValueError(
                    "Conflicting AWS credentials configured. Keep only one credential pair "
                    "or make both naming schemes match."
                )
            return standard_access, standard_secret
        raise ValueError(
            "Incomplete AWS credentials configured across standard and legacy env vars. "
            "Set one complete pair: AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or "
            "AWS_ACCESS_KEY/AWS_SECRET_KEY."
        )

    if standard_present:
        if not (standard_access and standard_secret):
            raise ValueError(
                "Incomplete AWS credentials. Set both AWS_ACCESS_KEY_ID and "
                "AWS_SECRET_ACCESS_KEY."
            )
        return standard_access, standard_secret

    if legacy_present:
        if not (legacy_access and legacy_secret):
            raise ValueError(
                "Incomplete AWS credentials. Set both AWS_ACCESS_KEY and AWS_SECRET_KEY."
            )
        return legacy_access, legacy_secret

    return "", ""


_AWS_ACCESS_KEY, _AWS_SECRET_KEY = _resolve_aws_credentials()


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
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://bbapp-front.vercel.app/",
        ).split(",")
        if origin.strip()
    ]
    aws_access_key: str = _AWS_ACCESS_KEY
    aws_secret_key: str = _AWS_SECRET_KEY
    aws_session_token: str = _getenv_stripped("AWS_SESSION_TOKEN")
    aws_region: str = _getenv_stripped("AWS_REGION")
    aws_bucket_name: str = _getenv_stripped("AWS_BUCKET_NAME")
    aws_public_base_url: str = _getenv_stripped("AWS_PUBLIC_BASE_URL").rstrip("/")
    s3_client_photo_prefix: str = (_getenv_stripped("S3_CLIENT_PHOTO_PREFIX") or "client-photos").strip("/")
    s3_generated_photo_prefix: str = (_getenv_stripped("S3_GENERATED_PHOTO_PREFIX") or "generated-images").strip("/")
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
