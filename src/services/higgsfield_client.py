from typing import Any

import httpx

from src.config import Settings


class HiggsfieldClient:
    base_url = "https://platform.higgsfield.ai"

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self.settings.authorization_header,
            "Accept": "application/json",
        }

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str,
        resolution: str,
        webhook_url: str | None,
        image_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.settings.has_higgsfield_credentials:
            raise ValueError("Higgsfield credentials are not configured")

        payload: dict[str, Any] = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if image_urls:
            # Higgsfield's Cloud API expects a structured `input_images` array of
            # `{type: "image_url", image_url: ...}` objects for multi-photo identity
            # references. A flat list of strings under `image_urls` is silently
            # ignored by the Soul endpoint, which is why only one photo was ever
            # reflected in the generation.
            payload["input_images"] = [
                {"type": "image_url", "image_url": url} for url in image_urls
            ]
        params = {"hf_webhook": webhook_url} if webhook_url else None
        model_id = self.settings.hf_image_model_id.strip().strip("/")

        async with httpx.AsyncClient(timeout=self.settings.hf_timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/{model_id}",
                json=payload,
                headers=self._headers,
                params=params,
            )

        if response.status_code >= 400:
            raise RuntimeError(f"Higgsfield image generation failed: {response.text}")

        data = response.json()
        return {
            "request_id": data.get("request_id") or data.get("id"),
            "status": data.get("status", "queued"),
            "status_url": data.get("status_url"),
            "cancel_url": data.get("cancel_url"),
            "raw_response": data,
        }

    async def get_request_status(self, status_url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.settings.hf_timeout_seconds) as client:
            response = await client.get(status_url, headers=self._headers)

        if response.status_code >= 400:
            raise RuntimeError(f"Higgsfield status request failed: {response.text}")

        return response.json()

    async def cancel_image(self, cancel_url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.settings.hf_timeout_seconds) as client:
            response = await client.post(cancel_url, headers=self._headers)

        if response.status_code >= 400:
            raise RuntimeError(f"Higgsfield cancel request failed: {response.text}")

        return response.json()
