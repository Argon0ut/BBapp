import asyncio
from pathlib import Path
from types import SimpleNamespace

from src.services.client_photo_service import ClientPhotoService


class DummyImageStorageService:
    def __init__(
        self,
        public_base_url: str = "",
        *,
        enabled: bool = False,
        s3_url: str = "",
        photo_content: dict[str, tuple[bytes, str]] | None = None,
    ):
        self.settings = SimpleNamespace(
            public_base_url=public_base_url,
            s3_presigned_ttl_seconds=3600,
        )
        self.enabled = enabled
        self._s3_url = s3_url
        self._photo_content = photo_content or {}

    def extract_key_from_stored_value(self, stored_value):
        return (stored_value or "").lstrip("/")

    def extract_file_name(self, stored_value):
        return Path(self.extract_key_from_stored_value(stored_value)).name

    def build_client_photo_key(self, user_id: int, file_name: str) -> str:
        return f"client-photos/user_{user_id}/{file_name}"

    async def get_client_photo_url(self, key: str) -> str:
        return self._s3_url

    async def get_client_photo_content(self, key: str) -> tuple[bytes, str]:
        return self._photo_content.get(key, (b"", "application/octet-stream"))


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


class StubClientPhotosRepo:
    def __init__(self, photos):
        self._photos = photos

    async def get_one(self, user_id):
        return [photo for photo in self._photos if photo.user_id == user_id]


def test_get_provider_photo_payloads_returns_bytes_for_each_photo():
    photos = [
        SimpleNamespace(
            user_id=7,
            photo_type="front",
            file_name="client-photos/user_7/front.png",
        ),
        SimpleNamespace(
            user_id=7,
            photo_type="right",
            file_name="client-photos/user_7/right.png",
        ),
    ]
    storage = DummyImageStorageService(
        enabled=True,
        photo_content={
            "client-photos/user_7/front.png": (b"front-bytes", "image/png"),
            "client-photos/user_7/right.png": (b"right-bytes", "image/png"),
        },
    )
    service = ClientPhotoService(
        client_photos_repo=StubClientPhotosRepo(photos),
        image_storage_service=storage,
    )

    payloads = asyncio.run(service.get_provider_photo_payloads(user_id=7))

    assert payloads == [
        ("front.png", b"front-bytes", "image/png"),
        ("right.png", b"right-bytes", "image/png"),
    ]
