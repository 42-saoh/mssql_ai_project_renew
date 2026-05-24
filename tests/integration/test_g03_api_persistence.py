from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from apps.api.api_app.repositories import approval_repository, artifact_repository, conversation_repository, run_repository, validation_repository


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def test_chat_routes_persist_and_read_sanitized_chat_run():
    _clear_repositories()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/chat-runs",
        json={
            "conversationId": "conv_contract",
            "actorId": "analyst-1",
            "message": "Show dependency information for the order table",
        },
    )

    body = created.json()
    assert created.status_code == 200
    assert body["status"] == "ACCEPTED"
    assert body["route"] == "codex_runner"

    fetched = client.get(f"/api/v1/chat-runs/{body['chatRunId']}").json()
    assert fetched["messageSummary"] == "DEPENDENCY_ANALYSIS request summary."
    assert "Show dependency information" not in str(fetched)

    conversation = client.get("/api/v1/conversations/conv_contract").json()
    assert conversation["conversationId"] == "conv_contract"
    assert conversation["items"][0]["chatRunId"] == body["chatRunId"]


def test_blocked_route_can_resume_policy_approval_without_artifacts():
    _clear_repositories()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/chat-runs",
        json={"message": "Please apply this DDL"},
    ).json()

    assert created["status"] == "BLOCKED"
    assert created["policyDecision"] == "BLOCKED_OR_APPROVAL_REQUIRED"
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []

    resumed = client.post(f"/api/v1/approvals/{created['approvalId']}/resume").json()
    assert resumed == {"approvalId": created["approvalId"], "status": "RESUMED"}
