import pytest

from src.config import Settings
from src.services.higgsfield_client import HiggsfieldClient


class DummyResponse:
    status_code = 200
    text = ""

    def json(self):
        return {
            "status": "queued",
            "request_id": "req-1",
            "status_url": "https://platform.higgsfield.ai/requests/req-1/status",
            "cancel_url": "https://platform.higgsfield.ai/requests/req-1/cancel",
        }


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict | None = None, headers: dict | None = None, params: dict | None = None):
        DummyAsyncClient.last_request = {
            "url": url,
            "json": json,
            "headers": headers,
            "params": params,
        }
        return DummyResponse()


@pytest.mark.asyncio
async def test_generate_image_uses_model_path_and_query_param_for_webhook(monkeypatch):
    monkeypatch.setattr("src.services.higgsfield_client.httpx.AsyncClient", DummyAsyncClient)
    settings = Settings(
        hf_api_key="api-key",
        hf_secret_key="secret-key",
        hf_image_model_id="higgsfield-ai/soul/standard",
    )
    client = HiggsfieldClient(settings)

    response = await client.generate_image(
        prompt="short bob haircut",
        aspect_ratio="1:1",
        resolution="720p",
        webhook_url="https://app.example.com/hairstyle-previews/webhooks/higgsfield-image",
        image_urls=[
            "https://storage.example/front.jpg",
            "https://storage.example/right.jpg",
        ],
    )

    assert response["request_id"] == "req-1"
    assert DummyAsyncClient.last_request["url"] == "https://platform.higgsfield.ai/higgsfield-ai/soul/standard"
    assert DummyAsyncClient.last_request["params"] == {
        "hf_webhook": "https://app.example.com/hairstyle-previews/webhooks/higgsfield-image"
    }
    assert DummyAsyncClient.last_request["json"] == {
        "prompt": "short bob haircut",
        "aspect_ratio": "1:1",
        "resolution": "720p",
        "input_images": [
            {"type": "image_url", "image_url": "https://storage.example/front.jpg"},
            {"type": "image_url", "image_url": "https://storage.example/right.jpg"},
        ],
    }
