import base64

import httpx

from src.config import Settings

_ENDPOINT = "https://api.openai.com/v1/images/edits"
_ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "landscape": "1536x1024",
    "2:3": "1024x1536",
    "portrait": "1024x1536",
}


class OpenAIImageClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def size_for_aspect_ratio(aspect_ratio: str) -> str:
        return _ASPECT_RATIO_TO_SIZE.get((aspect_ratio or "").strip(), "1024x1024")

    async def generate_image(
        self,
        *,
        prompt: str,
        aspect_ratio: str,
        image_payloads: list[tuple[str, bytes, str]],
    ) -> bytes:
        if not self.settings.openai_api_key:
            raise RuntimeError("OpenAI credentials are not configured")
        if not image_payloads:
            raise ValueError("At least one reference image is required")

        files = [
            ("image", (file_name or "reference.png", content, content_type or "image/png"))
            for file_name, content, content_type in image_payloads
        ]
        data = {
            "model": self.settings.openai_image_model,
            "prompt": prompt,
            "size": self.size_for_aspect_ratio(aspect_ratio),
        }
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}

        async with httpx.AsyncClient(timeout=self.settings.openai_timeout_seconds) as client:
            response = await client.post(
                _ENDPOINT,
                data=data,
                files=files,
                headers=headers,
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenAI image edit failed ({response.status_code}): {response.text}"
            )

        payload = response.json()
        data_items = payload.get("data") or []
        if not data_items:
            raise RuntimeError("OpenAI image response did not include image data")

        b64 = data_items[0].get("b64_json")
        if not b64:
            raise RuntimeError("OpenAI image response did not include image data")
        return base64.b64decode(b64)
