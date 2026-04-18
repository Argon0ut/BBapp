import base64
from types import SimpleNamespace

import pytest

from src.config import Settings
from src.services.openai_image_client import OpenAIImageClient


class DummyImagesAPI:
    last_request = None

    async def edit(self, **kwargs):
        DummyImagesAPI.last_request = kwargs
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    b64_json=base64.b64encode(b"generated-png-bytes").decode("ascii")
                )
            ]
        )


class DummyAsyncOpenAI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.images = DummyImagesAPI()


@pytest.mark.asyncio
async def test_generate_image_uses_openai_image_edit_api(monkeypatch):
    monkeypatch.setattr(
        "src.services.openai_image_client.AsyncOpenAI",
        DummyAsyncOpenAI,
    )
    settings = Settings(
        openai_api_key="api-key",
        openai_image_model="gpt-image-1",
    )
    client = OpenAIImageClient(settings)

    response = await client.generate_image(
        prompt="short bob haircut",
        aspect_ratio="3:2",
        image_contents=[
            (b"front-bytes", "image/jpeg", "front.jpg"),
            (b"right-bytes", "image/png", "right.png"),
        ],
    )

    assert response == {
        "content": b"generated-png-bytes",
        "content_type": "image/png",
    }
    assert DummyImagesAPI.last_request["model"] == "gpt-image-1"
    assert DummyImagesAPI.last_request["prompt"] == "short bob haircut"
    assert DummyImagesAPI.last_request["size"] == "1536x1024"
    assert DummyImagesAPI.last_request["n"] == 1
    assert DummyImagesAPI.last_request["input_fidelity"] == "high"

    image_payload = DummyImagesAPI.last_request["image"]
    assert len(image_payload) == 2
    assert image_payload[0][0] == "front.jpg"
    assert image_payload[0][2] == "image/jpeg"
    assert image_payload[1][0] == "right.png"
    assert image_payload[1][2] == "image/png"
