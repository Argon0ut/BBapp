from copy import deepcopy
from datetime import datetime, timezone

_preview_requests: list[dict] = []


class HairstylePreviewRepository:
    async def add(self, request: dict):
        _preview_requests.append(request)
        return deepcopy(request)

    async def get(self, request_id: int):
        for request in _preview_requests:
            if request["id"] == request_id:
                return deepcopy(request)
        return None

    async def update(self, request_id: int, updates: dict):
        now = datetime.now(timezone.utc)
        for request in _preview_requests:
            if request["id"] == request_id:
                request.update(updates)
                request["updated_at"] = now
                return deepcopy(request)
        return None

    async def get_by_provider_request_id(self, provider_request_id: str):
        for request in _preview_requests:
            if request.get("provider_request_id") == provider_request_id:
                return deepcopy(request)
        return None

    async def clear(self):
        _preview_requests.clear()

    async def _next_id(self):
        if not _preview_requests:
            return 0
        return _preview_requests[-1]["id"] + 1
