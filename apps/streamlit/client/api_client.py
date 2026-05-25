from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


class ApiClient:
    def __init__(self, base_url: str | None = None, requester: Any | None = None):
        self.base_url = (
            base_url
            or os.getenv("PLF_API_BASE_URL")
            or os.getenv("PLF_API_URL")
            or "http://localhost:8000"
        ).rstrip("/")
        self._requester = requester if requester is not None else requests

    def create_chat_run(
        self,
        message: str,
        *,
        conversation_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message}
        if conversation_id:
            payload["conversationId"] = conversation_id
        if actor_id:
            payload["actorId"] = actor_id
        return self._post("/api/v1/chat-runs", payload)

    def get_chat_run(self, chat_run_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/chat-runs/{_path_part(chat_run_id)}")

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/conversations/{_path_part(conversation_id)}")

    def list_artifacts(self) -> dict[str, Any]:
        return self._get("/api/v1/artifacts")

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        return self._get(f"/api/v1/artifacts/{_path_part(artifact_id)}")

    def get_health(self) -> dict[str, Any]:
        return self._get("/health")

    def metadata_ready(self) -> dict[str, Any]:
        return self._get("/api/v1/metadata/ready")

    def list_metadata_tools(self) -> dict[str, Any]:
        return self._get("/api/v1/metadata/tools")

    def _get(self, path: str) -> dict[str, Any]:
        return self._request("get", path)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("post", path, json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if self._requester is None:
            return _offline(path, "FastAPI client dependency is unavailable.", "ImportError")
        try:
            request_method = getattr(self._requester, method)
            response = request_method(f"{self.base_url}{path}", timeout=30, **kwargs)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return _offline(path, "FastAPI request failed.", exc.__class__.__name__)
        if isinstance(data, dict):
            return data
        return {"ok": True, "data": data}


def _path_part(value: str) -> str:
    return quote(value.strip(), safe="")


def _offline(path: str, message: str, error_class: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "OFFLINE",
        "path": path,
        "error": {
            "message": message,
            "errorClass": error_class,
        },
    }
