from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    run_repository,
    validation_repository,
)


def _clear_repositories() -> None:
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def _valid_proposal() -> dict:
    return {
        "artifactType": "DEPENDENCY_REPORT",
        "title": "Dependency report",
        "contentMarkdown": "Generated dependency report. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }


def test_g10_artifact_validation_routes_persist_and_read_review_metadata():
    _clear_repositories()
    client = TestClient(create_app())

    persisted = client.post(
        "/api/v1/artifacts/validated",
        json={
            "chatRunId": "chatrun_1",
            "codexRunId": "codexrun_1",
            "proposal": _valid_proposal(),
        },
    ).json()

    assert persisted["status"] == "PERSISTED"
    artifact_id = persisted["artifact"]["artifactId"]

    detail = client.get(f"/api/v1/artifacts/{artifact_id}").json()
    validations = client.get(f"/api/v1/artifacts/{artifact_id}/validations").json()
    listing = client.get("/api/v1/artifacts").json()

    assert detail["validationStatus"] == "VALIDATED"
    assert detail["productionReady"] is False
    assert "contentMarkdown" not in str(detail)
    assert validations["items"][0]["policyValid"] is True
    assert listing["items"][0]["artifactId"] == artifact_id


def test_g10_conversation_history_route_returns_sanitized_summaries():
    _clear_repositories()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/chat-runs",
        json={
            "conversationId": "conv_g10",
            "actorId": "analyst-1",
            "message": "Show dependency information for dbo.Orders",
        },
    ).json()

    assert created["status"] == "ACCEPTED"
    conversations = client.get("/api/v1/conversations").json()
    detail = client.get("/api/v1/conversations/conv_g10").json()
    rendered = str({"conversations": conversations, "detail": detail})

    assert conversations["items"][0]["conversationId"] == "conv_g10"
    assert conversations["items"][0]["runCount"] == 1
    assert detail["items"][0]["messageSummary"] == "DEPENDENCY_ANALYSIS request summary."
    assert "Show dependency information" not in rendered
    assert "dbo.Orders" not in rendered


def test_g10_approval_routes_list_get_and_resume_without_side_effects():
    _clear_repositories()
    client = TestClient(create_app())

    created = client.post("/api/v1/chat-runs", json={"message": "Please apply this DDL"}).json()
    approval_id = created["approvalId"]

    approvals = client.get("/api/v1/approvals").json()
    approval = client.get(f"/api/v1/approvals/{approval_id}").json()
    resumed = client.post(f"/api/v1/approvals/{approval_id}/resume").json()

    assert approvals["items"][0]["approvalId"] == approval_id
    assert approval["status"] == "PENDING"
    assert resumed == {"approvalId": approval_id, "status": "RESUMED"}
    assert client.get(f"/api/v1/approvals/{approval_id}").json()["status"] == "RESUMED"
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []
