import asyncio
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
from botocore.config import Config

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
                aws_session_token=settings.aws_session_token or None,
                region_name=settings.aws_region,
                config=Config(signature_version="s3v4"),
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

    async def get_object_url(self, key: str) -> str:
        if not self._client:
            return key
        if self.settings.aws_public_base_url:
            return self._public_url_for_key(key)

        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self.settings.aws_bucket_name, "Key": key},
            ExpiresIn=self.settings.s3_presigned_ttl_seconds,
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
        return await self.get_object_url(key)

    async def delete_client_photo(self, key: str) -> None:
        if self._client:
            await asyncio.to_thread(
                self._client.delete_object,
                Bucket=self.settings.aws_bucket_name,
                Key=key,
            )
            return

        local_path = Path(key)
        try:
            await asyncio.to_thread(local_path.unlink)
        except FileNotFoundError:
            return

    async def get_client_photo_content(self, key: str) -> tuple[bytes, str]:
        if self._client:
            response = await asyncio.to_thread(
                self._client.get_object,
                Bucket=self.settings.aws_bucket_name,
                Key=key,
            )
            body = await asyncio.to_thread(response["Body"].read)
            content_type = response.get("ContentType") or self._guess_content_type(key)
            return body, content_type

        local_path = Path(key)
        body = await asyncio.to_thread(local_path.read_bytes)
        return body, self._guess_content_type(key)

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

    @staticmethod
    def _guess_content_type(path: str) -> str:
        guessed, _ = mimetypes.guess_type(path)
        return guessed or "application/octet-stream"

    async def store_generated_image(
        self,
        preview_id: int,
        content: bytes,
        content_type: str = "image/png",
    ) -> str:
        normalized_type = (content_type or "image/png").split(";")[0].strip().lower()
        extension = _EXT_BY_CONTENT_TYPE.get(normalized_type, "png")

        relative_path = (
            f"{self.settings.s3_generated_photo_prefix}/"
            f"preview_{preview_id}_{uuid4().hex}.{extension}"
        )

        if self._client:
            await self.upload_bytes(key=relative_path, content=content, content_type=normalized_type)
            return await self.get_object_url(relative_path)

        local_path = Path(relative_path)
        await asyncio.to_thread(local_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(local_path.write_bytes, content)
        return str(local_path)

    def is_managed_storage_url(
        self,
        stored_value: str | None,
        *,
        expected_prefix: str | None = None,
    ) -> bool:
        raw_value = (stored_value or "").strip()
        if not raw_value or not self._client:
            return False

        key = self.extract_key_from_stored_value(raw_value)
        if not key:
            return False

        if expected_prefix:
            normalized_prefix = expected_prefix.strip("/")
            if key != normalized_prefix and not key.startswith(f"{normalized_prefix}/"):
                return False

        if "://" not in raw_value:
            return True

        parsed = urlparse(raw_value)
        if not parsed.netloc:
            return False

        managed_hosts = set()
        if self.settings.aws_public_base_url:
            public_host = urlparse(self.settings.aws_public_base_url).netloc
            if public_host:
                managed_hosts.add(public_host)

        bucket_host = (
            f"{self.settings.aws_bucket_name}.s3.{self.settings.aws_region}.amazonaws.com"
            if self.settings.aws_bucket_name and self.settings.aws_region
            else ""
        )
        if bucket_host:
            managed_hosts.add(bucket_host)

        return parsed.netloc in managed_hosts

    async def refresh_managed_storage_url(
        self,
        stored_value: str | None,
        *,
        expected_prefix: str | None = None,
    ) -> str | None:
        if not stored_value:
            return stored_value
        if not self.is_managed_storage_url(stored_value, expected_prefix=expected_prefix):
            return stored_value

        key = self.extract_key_from_stored_value(stored_value)
        return await self.get_object_url(key)

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
