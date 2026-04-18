import base64
import io
from typing import Any

import httpx
from openai import AsyncOpenAI, OpenAIError

from src.config import Settings

_ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "2:3": "1024x1536",
    "3:4": "1024x1536",
    "9:16": "1024x1536",
    "3:2": "1536x1024",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
}

_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class OpenAIImageClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: AsyncOpenAI | None = (
            AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    async def generate_image(
        self,
        prompt: str,
        image_contents: list[tuple[bytes, str, str]],
        aspect_ratio: str | None = None,
    ) -> dict[str, Any]:
        if not self._client:
            raise ValueError("OpenAI credentials are not configured")
        if not image_contents:
            raise ValueError("At least one reference image is required")

        size = _ASPECT_RATIO_TO_SIZE.get((aspect_ratio or "").strip(), "auto")

        image_files: list[tuple[str, io.BytesIO, str]] = []
        for idx, (content, content_type, file_name) in enumerate(image_contents):
            normalized_content_type = (content_type or "image/png").split(";")[0].strip().lower()
            extension = _EXT_BY_CONTENT_TYPE.get(normalized_content_type, "png")
            resolved_name = file_name or f"reference_{idx}.{extension}"
            image_files.append(
                (resolved_name, io.BytesIO(content), normalized_content_type)
            )

        edit_kwargs: dict[str, Any] = {
            "model": self.settings.openai_image_model,
            "image": image_files if len(image_files) > 1 else image_files[0],
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
        if self.settings.openai_image_model == "gpt-image-1":
            edit_kwargs["input_fidelity"] = "high"

        try:
            result = await self._client.images.edit(**edit_kwargs)
        except OpenAIError as exc:
            raise RuntimeError(f"OpenAI image generation failed: {exc}") from exc

        if not getattr(result, "data", None):
            raise RuntimeError("OpenAI returned no image data")

        entry = result.data[0]
        image_bytes, content_type = await self._extract_image_bytes(entry)

        return {
            "content": image_bytes,
            "content_type": content_type,
        }

    @staticmethod
    async def _extract_image_bytes(entry: Any) -> tuple[bytes, str]:
        b64_payload = getattr(entry, "b64_json", None)
        if b64_payload:
            return base64.b64decode(b64_payload), "image/png"

        image_url = getattr(entry, "url", None)
        if image_url:
            async with httpx.AsyncClient(timeout=60) as http_client:
                response = await http_client.get(image_url)
                response.raise_for_status()
            content_type = (response.headers.get("content-type") or "image/png").split(";")[0].strip().lower()
            return response.content, content_type

        raise RuntimeError("OpenAI response missing image data")
