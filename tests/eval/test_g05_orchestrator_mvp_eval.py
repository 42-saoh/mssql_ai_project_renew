from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import chat_service
from plf_agent_orchestration.graph import orchestrate_message

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def _case_ids(cases: list[dict]) -> set[str]:
    return {case["id"] for case in cases if "id" in case}


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def test_g05_orchestrator_eval_cases_are_declared():
    spec = _load_yaml("spec/development/langgraph_chat_orchestrator_mvp.yaml")

    for suite, expected_cases in spec["evalCases"].items():
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        assert suite_spec["name"] == suite
        missing_cases = set(expected_cases) - _case_ids(suite_spec["cases"])
        assert not missing_cases, f"{suite} missing G05 eval cases: {sorted(missing_cases)}"


def test_g05_eval_case_contract_matches_suite_g05_cases():
    spec = _load_yaml("spec/development/langgraph_chat_orchestrator_mvp.yaml")
    declared_cases = {
        case_id
        for expected_cases in spec["evalCases"].values()
        for case_id in expected_cases
    }

    assert declared_cases
    assert all(case_id.startswith("g05_") for case_id in declared_cases)

    for suite in spec["evalCases"]:
        suite_spec = _load_yaml(f"spec/eval/{suite}.yaml")
        suite_g05_cases = {
            case_id
            for case_id in _case_ids(suite_spec["cases"])
            if case_id.startswith("g05_")
        }
        undeclared_cases = suite_g05_cases - declared_cases
        assert not undeclared_cases, (
            f"{suite} has G05 eval cases not declared in "
            "spec/development/langgraph_chat_orchestrator_mvp.yaml: "
            f"{sorted(undeclared_cases)}"
        )


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
        "Describe table metadata",
        "Show me database tables",
        "List database procedures",
        "데이터베이스 테이블 보여줘",
        "테이블 목록 보여줘",
        "데이터베이스 프로시저 조회해줘",
        "프로시저 목록 보여줘",
        "모든 컬럼 조회해줘",
        "테이블들 조회해줘",
        "프로시저들 보여줘",
        "전체 데이터베이스 객체 검색해줘",
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
