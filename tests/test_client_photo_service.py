import asyncio
from types import SimpleNamespace

from src.services.client_photo_service import ClientPhotoService


class DummyImageStorageService:
    def __init__(
        self,
        public_base_url: str = "",
        *,
        enabled: bool = False,
        s3_url: str = "",
    ):
        self.settings = SimpleNamespace(
            public_base_url=public_base_url,
            s3_presigned_ttl_seconds=3600,
        )
        self.enabled = enabled
        self._s3_url = s3_url

    def build_signed_media_expires_at(self) -> int:
        return 1234567890

    def build_signed_media_token(self, subject: str, expires_at: int) -> str:
        return f"token-for:{subject}:{expires_at}"

    def extract_key_from_stored_value(self, stored_value):
        return (stored_value or "").lstrip("/")

    def extract_file_name(self, stored_value):
        from pathlib import Path
        return Path(self.extract_key_from_stored_value(stored_value)).name

    def build_client_photo_key(self, user_id: int, file_name: str) -> str:
        return f"client-photos/user_{user_id}/{file_name}"

    async def get_client_photo_url(self, key: str) -> str:
        return self._s3_url


def test_build_file_url_uses_public_base_url():
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService("https://api.example.com/"),
    )
    photo = SimpleNamespace(user_id=7, photo_type="front", file_name="front.png")

    assert (
        asyncio.run(service._build_file_url(photo))
        == "https://api.example.com/clients/7/photos/front/file"
    )


def test_build_file_url_falls_back_to_relative_path():
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService(""),
    )
    photo = SimpleNamespace(user_id=7, photo_type="rear", file_name="rear.png")

    assert asyncio.run(service._build_file_url(photo)) == "/clients/7/photos/rear/file"


def test_build_file_url_returns_s3_url_when_storage_enabled():
    s3_url = "https://bucket.s3.us-east-1.amazonaws.com/client-photos/user_7/front.png?X-Amz-Signature=abc"
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService(
            "https://ngrok.example",
            enabled=True,
            s3_url=s3_url,
        ),
    )
    photo = SimpleNamespace(
        user_id=7,
        photo_type="front",
        file_name="client-photos/user_7/front.png",
    )

    assert asyncio.run(service._build_file_url(photo)) == s3_url


def test_build_provider_file_url_uses_signed_public_path():
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService("https://api.example.com/"),
    )
    photo = SimpleNamespace(user_id=7, photo_type="front", file_name="front.png")

    assert service._build_provider_file_url(photo) == (
        "https://api.example.com/clients/7/photos/front/provider-file"
        "?expires_at=1234567890&token=token-for:client-photo:7:front:1234567890"
    )
