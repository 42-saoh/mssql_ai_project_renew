from __future__ import annotations

import os
from typing import Any

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (
            base_url
            or os.getenv("PLF_API_BASE_URL")
            or os.getenv("PLF_API_URL")
            or "http://localhost:8000"
        )

    def create_chat_run(self, message: str) -> dict[str, Any]:
        if requests is None:
            return {"status": "OFFLINE", "message": "FastAPI client dependency is unavailable."}
        response = requests.post(f"{self.base_url}/api/v1/chat-runs", json={"message": message}, timeout=30)
        response.raise_for_status()
        return response.json()
