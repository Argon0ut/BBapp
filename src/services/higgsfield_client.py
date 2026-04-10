from typing import Any

import httpx

from src.config import Settings


class HiggsfieldClient:
    base_url = "https://api.higgsfield.ai"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str,
        resolution: str,
        webhook_url: str | None,
    ) -> dict[str, Any]:
        if not self.settings.has_higgsfield_credentials:
            raise ValueError("Higgsfield credentials are not configured")

        payload: dict[str, Any] = {
            "model": self.settings.hf_image_model_id,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if webhook_url:
            payload["hf_webhook"] = webhook_url

        headers = {"Authorization": self.settings.authorization_header}

        async with httpx.AsyncClient(timeout=self.settings.hf_timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/v1/text-to-image",
                json=payload,
                headers=headers,
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

    async def cancel_image(self, cancel_url: str) -> dict[str, Any]:
        headers = {"Authorization": self.settings.authorization_header}

        async with httpx.AsyncClient(timeout=self.settings.hf_timeout_seconds) as client:
            response = await client.post(cancel_url, headers=headers)

        if response.status_code >= 400:
            raise RuntimeError(f"Higgsfield cancel request failed: {response.text}")

        return response.json()
