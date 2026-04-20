import base64

from openai import AsyncOpenAI

from src.config import Settings

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
        self._client = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.openai_timeout_seconds,
            )

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
        if not self._client:
            raise RuntimeError("OpenAI credentials are not configured")
        if not image_payloads:
            raise ValueError("At least one reference image is required")

        images = [
            (file_name or "reference.png", content, content_type or "image/png")
            for file_name, content, content_type in image_payloads
        ]

        response = await self._client.images.edit(
            model=self.settings.openai_image_model,
            prompt=prompt,
            image=images,
            size=self.size_for_aspect_ratio(aspect_ratio),
        )

        b64 = response.data[0].b64_json
        if not b64:
            raise RuntimeError("OpenAI image response did not include image data")
        return base64.b64decode(b64)
