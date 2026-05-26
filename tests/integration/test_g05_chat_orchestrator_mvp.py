from __future__ import annotations

import pytest

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import chat_service


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def test_chat_service_persists_sanitized_checkpoint_and_fake_runner_metadata_only():
    _clear_repositories()
    message = "Show dependency information for the order table"

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "ACCEPTED"
    assert response["route"] == "codex_runner"
    assert response["fakeRunner"] == {"status": "SUCCEEDED", "proposalCount": 1}
    assert "codexRunId" in response
    assert message not in str(response["checkpoint"])

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run is not None
    assert stored_run["orchestrator_checkpoint"]["route"] == "codex_runner"
    assert stored_run["orchestrator_checkpoint"]["runnerRequest"]["mode"] == "fake"
    assert message not in str(stored_run)

    codex_run = run_repository.get_codex_run(response["codexRunId"])
    assert codex_run["runner_mode"] == "fake"
    assert codex_run["fake_runner_status"] == "SUCCEEDED"
    assert codex_run["fake_runner_proposal_count"] == 1
    assert "contentMarkdown" not in str(codex_run)
    assert artifact_repository.list_all() == []


def test_hard_blocked_chat_has_checkpoint_without_downstream_side_effects():
    _clear_repositories()

    response = chat_service.create_chat_run(
        "execute procedure dbo.ProcessOrder", actor_id="analyst-1"
    )

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in response["blockers"]
    assert "codexRunId" not in response
    assert "approvalId" not in response

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run["orchestrator_checkpoint"]["route"] == "blocked"
    assert "runnerRequest" not in stored_run["orchestrator_checkpoint"]
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []


@pytest.mark.parametrize("message", ["What is SQL?", "Explain databases"])
def test_db_themed_general_chat_has_no_downstream_side_effects(monkeypatch, message):
    _clear_repositories()

    def fail_metadata_search(*_args, **_kwargs):
        raise AssertionError(
            "metadata gateway must not be called for DB-themed general chat"
        )

    monkeypatch.setattr(
        chat_service.metadata_service, "search_metadata", fail_metadata_search
    )

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["intent"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert "OUT_OF_DOMAIN" in response["blockers"]
    assert response["pgptUsed"] is False
    assert "metadataSearch" not in response
    assert "codexRunId" not in response
    assert "approvalId" not in response

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run["orchestrator_checkpoint"]["route"] == "blocked"
    assert "runnerRequest" not in stored_run["orchestrator_checkpoint"]
    assert message not in str(stored_run)
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []


@pytest.mark.parametrize(
    ("message", "blocker"),
    [
        ("select name from dbo.Customer", "FREE_SQL_EXECUTION_BLOCKED"),
        ("show customer rows", "ROW_DATA_ACCESS_BLOCKED"),
        ("show sample data for dbo.Customer", "ROW_DATA_ACCESS_BLOCKED"),
        (
            "\uace0\uac1d \ud589 \ub370\uc774\ud130\ub97c \ubcf4\uc5ec\uc918",
            "ROW_DATA_ACCESS_BLOCKED",
        ),
    ],
)
def test_free_sql_and_row_data_chat_have_no_downstream_side_effects(message, blocker):
    _clear_repositories()

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert blocker in response["blockers"]
    assert response["pgptUsed"] is False
    assert "codexRunId" not in response
    assert "approvalId" not in response

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run is not None
    assert stored_run["user_message_summary"] == "Blocked request summary."
    assert stored_run["orchestrator_checkpoint"]["route"] == "blocked"
    assert message not in str(stored_run)
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []
