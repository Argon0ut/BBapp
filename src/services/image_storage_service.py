import asyncio
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
import httpx

from src.config import Settings

_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class ImageStorageService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        if settings.has_s3_credentials:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key,
                aws_secret_access_key=settings.aws_secret_key,
                region_name=settings.aws_region,
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _public_url_for_key(self, key: str) -> str:
        if self.settings.aws_public_base_url:
            return f"{self.settings.aws_public_base_url}/{key}"
        return (
            f"https://{self.settings.aws_bucket_name}.s3."
            f"{self.settings.aws_region}.amazonaws.com/{key}"
        )

    async def upload_bytes(self, key: str, content: bytes, content_type: str) -> str:
        if not self._client:
            raise RuntimeError("S3 storage is not configured")

        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.settings.aws_bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return key

    async def get_client_photo_url(self, key: str) -> str:
        if not self._client:
            return key

        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.settings.aws_bucket_name, "Key": key},
            ExpiresIn=self.settings.s3_presigned_ttl_seconds,
        )

    async def upload_client_photo(
        self,
        user_id: int,
        photo_type: str,
        extension: str,
        content: bytes,
        content_type: str,
    ) -> str:
        file_name = f"{photo_type}_{uuid4().hex}.{extension}"
        key = self.build_client_photo_key(user_id=user_id, file_name=file_name)
        await self.upload_bytes(key=key, content=content, content_type=content_type)
        return key

    def build_client_photo_key(self, user_id: int, file_name: str) -> str:
        return f"{self.settings.s3_client_photo_prefix}/user_{user_id}/{file_name}"

    async def mirror_generated_image(self, preview_id: int, source_url: str) -> str:
        if not self._client:
            return source_url

        async with httpx.AsyncClient(timeout=self.settings.hf_webhook_timeout_seconds) as client:
            response = await client.get(source_url)
            response.raise_for_status()

        raw_content_type = response.headers.get("content-type", "image/jpeg")
        content_type = raw_content_type.split(";")[0].strip().lower()
        extension = _EXT_BY_CONTENT_TYPE.get(content_type)

        if not extension:
            extension = Path(source_url).suffix.lower().lstrip(".") or "jpg"
            content_type = f"image/{extension if extension != 'jpg' else 'jpeg'}"

        key = (
            f"{self.settings.s3_generated_photo_prefix}/"
            f"preview_{preview_id}_{uuid4().hex}.{extension}"
        )
        await self.upload_bytes(key=key, content=response.content, content_type=content_type)
        return self._public_url_for_key(key)

    @staticmethod
    def extract_key_from_stored_value(stored_value: str | None) -> str:
        raw_value = (stored_value or "").strip()
        if not raw_value:
            return ""

        if "://" not in raw_value:
            return raw_value.lstrip("/")

        parsed = urlparse(raw_value)
        return parsed.path.lstrip("/")

    @staticmethod
    def extract_file_name(stored_value: str | None) -> str:
        return Path(ImageStorageService.extract_key_from_stored_value(stored_value)).name
