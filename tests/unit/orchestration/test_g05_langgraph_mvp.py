from __future__ import annotations

import pytest

from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_orchestration.pgpt_client import PgptClassification, PgptSettings


class CountingPgpt:
    def __init__(self, classification: PgptClassification | None = None):
        self.settings = PgptSettings(api_key="secret", enabled=True)
        self.classification = classification or PgptClassification(
            intent=Intent.DEPENDENCY_ANALYSIS,
            confidence=0.9,
            reason_summary="Dependency evidence request.",
        )
        self.calls: list[str] = []

    def classify_message(self, message: str):
        self.calls.append(message)
        return self.classification


def test_langgraph_orchestrator_routes_allowed_runner_intent_with_safe_checkpoint():
    message = "Show dependency information for the order table"
    pgpt = CountingPgpt()

    result = orchestrate_message(
        message, pgpt_client=pgpt, conversation_id="conv_1", chat_run_id="chatrun_1"
    )

    assert result["intent"] == "DEPENDENCY_ANALYSIS"
    assert result["policyDecision"] == "ALLOW"
    assert result["route"] == "codex_runner"
    assert result["runnerRequest"] == {
        "runType": "DEPENDENCY_ANALYSIS",
        "target": {"targetKey": "unresolved"},
        "mode": "fake",
    }
    assert result["orchestrator"]["engine"] == "langgraph"
    assert result["orchestrator"]["nodes"] == [
        "domain_guard",
        "policy_gate",
        "pgpt_intent_assist",
        "route_intent",
        "prepare_fake_runner",
    ]
    assert result["checkpoint"]["schemaVersion"] == "OrchestratorCheckpoint.v1"
    assert result["checkpoint"]["chatRunId"] == "chatrun_1"
    assert message not in str(result["checkpoint"])


def test_domain_guard_blocks_general_chat_before_pgpt_or_runner():
    pgpt = CountingPgpt()

    result = orchestrate_message("Recommend lunch today", pgpt_client=pgpt)

    assert result["intent"] == "BLOCKED"
    assert result["policyDecision"] == "BLOCKED"
    assert result["route"] == "blocked"
    assert result["runnerRequest"] is None
    assert result["pgptUsed"] is False
    assert result["pgptFallbackReason"] == "POLICY_BLOCKED_BEFORE_PGPT"
    assert pgpt.calls == []


@pytest.mark.parametrize(
    "message",
    [
        "What is SQL?",
        "Explain databases",
        "What is a column?",
        "Explain table metadata",
        "Describe table metadata",
        "Show me database tables",
        "List database procedures",
        "Describe SQL metadata",
        "Get procedure metadata",
    ],
)
def test_domain_guard_blocks_db_themed_general_chat_before_pgpt_or_runner(message):
    pgpt = CountingPgpt()

    result = orchestrate_message(message, pgpt_client=pgpt)

    assert result["intent"] == "BLOCKED"
    assert result["policyDecision"] == "BLOCKED"
    assert result["route"] == "blocked"
    assert "OUT_OF_DOMAIN" in result["blockers"]
    assert result["runnerRequest"] is None
    assert result["pgptUsed"] is False
    assert result["pgptFallbackReason"] == "POLICY_BLOCKED_BEFORE_PGPT"
    assert pgpt.calls == []


def test_hard_policy_gate_blocks_stored_procedure_execution_before_pgpt_or_runner():
    pgpt = CountingPgpt()

    result = orchestrate_message("execute procedure dbo.ProcessOrder", pgpt_client=pgpt)

    assert result["intent"] == "BLOCKED_OR_APPROVAL_REQUIRED"
    assert result["policyDecision"] == "BLOCKED"
    assert result["route"] == "blocked"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in result["blockers"]
    assert result["runnerRequest"] is None
    assert result["pgptUsed"] is False
    assert pgpt.calls == []


@pytest.mark.parametrize(
    ("message", "blocker"),
    [
        ("select name from dbo.Customer", "FREE_SQL_EXECUTION_BLOCKED"),
        (
            "run query select customer_id from dbo.Customer",
            "FREE_SQL_EXECUTION_BLOCKED",
        ),
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
        (
            "SQL \uc2e4\ud589: select name from dbo.Customer",
            "FREE_SQL_EXECUTION_BLOCKED",
        ),
    ],
)
def test_hard_policy_gate_blocks_free_sql_and_row_data_before_pgpt_or_runner(
    message, blocker
):
    pgpt = CountingPgpt()

    result = orchestrate_message(message, pgpt_client=pgpt)

    assert result["intent"] == "BLOCKED_OR_APPROVAL_REQUIRED"
    assert result["policyDecision"] == "BLOCKED"
    assert result["route"] == "blocked"
    assert blocker in result["blockers"]
    assert result["runnerRequest"] is None
    assert result["pgptUsed"] is False
    assert result["pgptFallbackReason"] == "POLICY_BLOCKED_BEFORE_PGPT"
    assert pgpt.calls == []


def test_english_sp_analysis_routes_to_runner_without_execution_language():
    result = orchestrate_message("Please analyze stored procedure PPM.dbo.InvoiceAudit")

    assert result["intent"] == "SP_ANALYSIS"
    assert result["policyDecision"] == "ALLOW"
    assert result["route"] == "codex_runner"
