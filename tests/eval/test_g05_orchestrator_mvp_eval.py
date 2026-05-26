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
from plf_agent_orchestration.graph import orchestrate_message


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


@pytest.mark.parametrize(
    ("message", "intent", "route"),
    [
        (
            "Please analyze stored procedure PPM.dbo.InvoiceAudit",
            "SP_ANALYSIS",
            "codex_runner",
        ),
        (
            "Show dependency information for the order table",
            "DEPENDENCY_ANALYSIS",
            "codex_runner",
        ),
        ("Create table design for order audit", "TABLE_DESIGN", "codex_runner"),
        ("Generate Java MyBatis mapper draft", "DRAFT_GENERATION", "codex_runner"),
        (
            "Find metadata for the order_id column",
            "METADATA_SEARCH",
            "metadata_gateway",
        ),
        ("Show history for this conversation", "HISTORY_LOOKUP", "history_store"),
    ],
)
def test_g05_supported_intents_route_to_expected_boundaries(message, intent, route):
    result = orchestrate_message(message)

    assert result["intent"] == intent
    assert result["policyDecision"] == "ALLOW"
    assert result["route"] == route


@pytest.mark.parametrize(
    "message",
    [
        "Recommend lunch today",
        "What is SQL?",
        "Explain databases",
    ],
)
def test_g05_general_chat_is_blocked_without_downstream_side_effects(message):
    _clear_repositories()

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["intent"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert response["pgptUsed"] is False
    assert "metadataSearch" not in response
    assert "codexRunId" not in response
    assert "approvalId" not in response
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []


@pytest.mark.parametrize(
    ("message", "blocker"),
    [
        ("select name from dbo.Customer", "FREE_SQL_EXECUTION_BLOCKED"),
        ("show customer rows", "ROW_DATA_ACCESS_BLOCKED"),
        ("show customer records", "ROW_DATA_ACCESS_BLOCKED"),
        ("show sample data for dbo.Customer", "ROW_DATA_ACCESS_BLOCKED"),
        (
            "\uace0\uac1d \ud589 \ub370\uc774\ud130\ub97c \ubcf4\uc5ec\uc918",
            "ROW_DATA_ACCESS_BLOCKED",
        ),
        (
            "\uace0\uac1d \ub808\ucf54\ub4dc\ub97c \uc870\ud68c\ud574\uc918",
            "ROW_DATA_ACCESS_BLOCKED",
        ),
    ],
)
def test_g05_free_sql_and_row_data_requests_hard_block_before_downstream_routing(
    message, blocker
):
    _clear_repositories()

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert blocker in response["blockers"]
    assert response["pgptUsed"] is False
    assert "codexRunId" not in response
    assert "approvalId" not in response
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []
