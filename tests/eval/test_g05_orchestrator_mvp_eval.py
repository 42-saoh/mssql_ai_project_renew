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
        ("Please analyze stored procedure PPM.dbo.InvoiceAudit", "SP_ANALYSIS", "codex_runner"),
        ("Show dependency information for the order table", "DEPENDENCY_ANALYSIS", "codex_runner"),
        ("Create table design for order audit", "TABLE_DESIGN", "codex_runner"),
        ("Generate Java MyBatis mapper draft", "DRAFT_GENERATION", "codex_runner"),
        ("Find metadata for the order_id column", "METADATA_SEARCH", "metadata_gateway"),
        ("Show history for this conversation", "HISTORY_LOOKUP", "history_store"),
    ],
)
def test_g05_supported_intents_route_to_expected_boundaries(message, intent, route):
    result = orchestrate_message(message)

    assert result["intent"] == intent
    assert result["policyDecision"] == "ALLOW"
    assert result["route"] == route


def test_g05_general_chat_is_blocked_without_downstream_side_effects():
    _clear_repositories()

    response = chat_service.create_chat_run("Recommend lunch today", actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["intent"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert response["pgptUsed"] is False
    assert "codexRunId" not in response
    assert "approvalId" not in response
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []
