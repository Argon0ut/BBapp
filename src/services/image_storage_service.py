import asyncio
import hashlib
import hmac
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
import httpx
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

    def _media_signing_secret(self) -> bytes:
        raw_secret = (
            self.settings.hf_secret_key
            or self.settings.aws_secret_key
            or self.settings.aws_access_key
        )
        if not raw_secret:
            raise RuntimeError("A secret is required to sign media URLs")
        return raw_secret.encode("utf-8")

    def build_signed_media_expires_at(self) -> int:
        return int(time.time()) + self.settings.s3_presigned_ttl_seconds

    def build_signed_media_token(self, subject: str, expires_at: int) -> str:
        payload = f"{subject}:{expires_at}".encode("utf-8")
        return hmac.new(
            self._media_signing_secret(),
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify_signed_media_token(
        self,
        subject: str,
        expires_at: int,
        token: str | None,
    ) -> bool:
        if not token or expires_at < int(time.time()):
            return False

        expected = self.build_signed_media_token(subject=subject, expires_at=expires_at)
        return hmac.compare_digest(token, expected)

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
        return await self.get_object_url(key)

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
