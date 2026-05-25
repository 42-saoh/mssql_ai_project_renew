from __future__ import annotations

from apps.streamlit.client.api_client import ApiClient


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _FakeRequester:
    def __init__(self):
        self.calls = []

    def post(self, url, *, timeout, json):
        self.calls.append(("post", url, timeout, json))
        return _FakeResponse({"status": "ACCEPTED", "chatRunId": "chatrun_test"})

    def get(self, url, *, timeout):
        self.calls.append(("get", url, timeout, None))
        return _FakeResponse({"status": "ok", "items": []})


def test_api_client_prefers_plf_api_base_url(monkeypatch):
    monkeypatch.setenv("PLF_API_BASE_URL", "http://api:8000")
    monkeypatch.setenv("PLF_API_URL", "http://localhost:8000")

    assert ApiClient().base_url == "http://api:8000"


def test_api_client_falls_back_to_plf_api_url(monkeypatch):
    monkeypatch.delenv("PLF_API_BASE_URL", raising=False)
    monkeypatch.setenv("PLF_API_URL", "http://localhost:9000")

    assert ApiClient().base_url == "http://localhost:9000"


def test_api_client_routes_chat_runs_through_fastapi():
    requester = _FakeRequester()
    client = ApiClient(base_url="http://api:8000/", requester=requester)

    result = client.create_chat_run("Review dependencies", conversation_id="conv_1", actor_id="analyst")

    assert result["chatRunId"] == "chatrun_test"
    assert requester.calls == [
        (
            "post",
            "http://api:8000/api/v1/chat-runs",
            30,
            {"message": "Review dependencies", "conversationId": "conv_1", "actorId": "analyst"},
        )
    ]


def test_api_client_exposes_history_artifact_and_admin_eval_fastapi_methods():
    requester = _FakeRequester()
    client = ApiClient(base_url="http://api:8000", requester=requester)

    client.get_chat_run("run 1")
    client.list_conversations()
    client.get_conversation("conv 1")
    client.list_artifacts()
    client.get_artifact("artifact 1")
    client.list_artifact_validations("artifact 1")
    client.list_approvals()
    client.get_approval("approval 1")
    client.resume_approval("approval 1")
    client.get_health()
    client.metadata_ready()
    client.list_metadata_tools()

    assert [call[1] for call in requester.calls] == [
        "http://api:8000/api/v1/chat-runs/run%201",
        "http://api:8000/api/v1/conversations",
        "http://api:8000/api/v1/conversations/conv%201",
        "http://api:8000/api/v1/artifacts",
        "http://api:8000/api/v1/artifacts/artifact%201",
        "http://api:8000/api/v1/artifacts/artifact%201/validations",
        "http://api:8000/api/v1/approvals",
        "http://api:8000/api/v1/approvals/approval%201",
        "http://api:8000/api/v1/approvals/approval%201/resume",
        "http://api:8000/health",
        "http://api:8000/api/v1/metadata/ready",
        "http://api:8000/api/v1/metadata/tools",
    ]


def test_api_client_returns_offline_payload_when_dependency_is_missing():
    client = ApiClient(base_url="http://api:8000", requester=None)
    client._requester = None

    result = client.list_artifacts()

    assert result["status"] == "OFFLINE"
    assert result["path"] == "/api/v1/artifacts"
