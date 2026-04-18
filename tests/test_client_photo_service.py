from types import SimpleNamespace

from src.services.client_photo_service import ClientPhotoService


class DummyImageStorageService:
    def __init__(self, public_base_url: str = ""):
        self.settings = SimpleNamespace(public_base_url=public_base_url)


def test_build_file_url_uses_public_base_url():
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService("https://api.example.com/"),
    )
    photo = SimpleNamespace(user_id=7, photo_type="front", file_name="front.png")

    assert (
        service._build_file_url(photo)
        == "https://api.example.com/clients/7/photos/front/file"
    )


def test_build_file_url_falls_back_to_relative_path():
    service = ClientPhotoService(
        client_photos_repo=None,
        image_storage_service=DummyImageStorageService(""),
    )
    photo = SimpleNamespace(user_id=7, photo_type="rear", file_name="rear.png")

    assert service._build_file_url(photo) == "/clients/7/photos/rear/file"
