from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _spec() -> dict:
    return yaml.safe_load(
        _read("spec/development/langgraph_chat_orchestrator_mvp.yaml")
    )


def test_g05_langgraph_orchestrator_contract_files_exist():
    spec = _spec()

    assert spec["scope"] == "g05-langgraph-chat-orchestrator-mvp"
    assert (ROOT / spec["orchestrator"]["graphModule"]).exists()
    assert (ROOT / spec["orchestrator"]["stateModule"]).exists()
    assert (ROOT / spec["orchestrator"]["intentModule"]).exists()
    assert (ROOT / spec["orchestrator"]["policyGateModule"]).exists()
    assert (ROOT / spec["fakeRunnerRouting"]["gatewayModule"]).exists()
    assert (ROOT / spec["fakeRunnerRouting"]["fakeRunnerModule"]).exists()
    assert (ROOT / spec["apiIntegration"]["chatService"]).exists()


def test_g05_contract_preserves_policy_and_checkpoint_boundaries():
    spec = _spec()
    checkpoint = spec["checkpointState"]
    runner = spec["fakeRunnerRouting"]
    coverage = spec["policyGate"]["classifierCoverage"]

    assert spec["domainGuard"]["blocksGeneralChat"] is True
    assert spec["domainGuard"]["pgptMayNotAnswerGeneralChat"] is True
    assert spec["domainGuard"]["requiresSupportedActionOrLookupShape"] is True
    assert {
        "What is SQL?",
        "Explain databases",
        "What is a column?",
    } <= set(spec["domainGuard"]["dbThemedGeneralChatBlockedExamples"])
    assert spec["policyGate"]["blockedRequestsDoNotCallPgpt"] is True
    assert spec["policyGate"]["blockedRequestsDoNotSubmitRunner"] is True
    assert spec["policyGate"]["blockedRequestsDoNotPersistArtifacts"] is True
    assert checkpoint["rawUserMessageStored"] is False
    assert checkpoint["rawPromptStored"] is False
    assert checkpoint["rawProviderResponseStored"] is False
    assert checkpoint["rowDataStored"] is False
    assert checkpoint["secretsStored"] is False
    assert runner["actualRuntimeExecutionInG05"] is False
    assert runner["persistFakeRunnerProposalContent"] is False
    assert runner["persistArtifactProposalsInG05"] is False
    assert runner["productionReadyAllowed"] is False
    assert {
        "non_star_select_statement",
        "run_query_select_statement",
        "korean_sql_execution_phrase",
    } <= set(coverage["freeSqlExecution"])
    assert {
        "row_keyword_request",
        "record_keyword_request",
        "sample_data_request",
        "structured_row_data_payload",
        "korean_row_data_phrase",
    } <= set(coverage["rowDataAccess"])


def test_g05_graph_uses_declared_langgraph_nodes():
    spec = _spec()
    graph_text = _read(spec["orchestrator"]["graphModule"])

    assert "StateGraph" in graph_text
    assert "InMemorySaver" in graph_text
    for node_name in spec["orchestrator"]["graphNodes"]:
        assert node_name in graph_text


def test_g05_intent_routes_match_contract():
    spec = _spec()
    routes = spec["intentRouting"]

    assert routes["SP_ANALYSIS"] == "codex_runner"
    assert routes["DEPENDENCY_ANALYSIS"] == "codex_runner"
    assert routes["TABLE_DESIGN"] == "codex_runner"
    assert routes["DRAFT_GENERATION"] == "codex_runner"
    assert routes["METADATA_SEARCH"] == "metadata_gateway"
    assert routes["HISTORY_LOOKUP"] == "history_store"
    assert routes["BLOCKED"] == "blocked"
