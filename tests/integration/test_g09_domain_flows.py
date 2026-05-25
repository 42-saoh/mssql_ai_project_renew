from __future__ import annotations

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


def test_metadata_search_intent_calls_metadata_gateway_without_runner_or_artifact_side_effects(monkeypatch):
    _clear_repositories()
    captured = {}

    def fake_search(query, *, db_profile_id="master", object_types=None, limit=20):
        captured["query"] = query
        captured["db_profile_id"] = db_profile_id
        captured["object_types"] = object_types
        captured["limit"] = limit
        return {
            "ok": True,
            "toolName": "search_metadata_objects",
            "data": {"items": [{"objectName": "TB_ORDER", "objectType": "TABLE"}]},
        }

    monkeypatch.setattr(chat_service.metadata_service, "search_metadata", fake_search)

    response = chat_service.create_chat_run("Find order column metadata", actor_id="analyst-1")

    assert response["status"] == "ACCEPTED"
    assert response["intent"] == "METADATA_SEARCH"
    assert response["route"] == "metadata_gateway"
    assert response["metadataSearch"]["toolName"] == "search_metadata_objects"
    assert captured == {
        "query": "Find order column metadata",
        "db_profile_id": "master",
        "object_types": None,
        "limit": 20,
    }
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert approval_repository.list_all() == []

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run["user_message_summary"] == "Metadata search request summary."
    assert "Find order column metadata" not in str(stored_run)
    assert "TB_ORDER" not in str(stored_run)


def test_history_lookup_returns_prior_sanitized_runs_without_downstream_side_effects():
    _clear_repositories()
    first = chat_service.create_chat_run(
        "Show dependency information for the order table",
        conversation_id="conv_g09",
        actor_id="analyst-1",
    )

    history = chat_service.create_chat_run(
        "show history",
        conversation_id="conv_g09",
        actor_id="analyst-1",
    )

    assert history["status"] == "ACCEPTED"
    assert history["intent"] == "HISTORY_LOOKUP"
    assert history["route"] == "history_store"
    assert "codexRunId" not in history
    assert history["historyLookup"]["source"] == "history_store"
    assert [item["chatRunId"] for item in history["historyLookup"]["items"]] == [first["chatRunId"]]
    assert history["historyLookup"]["items"][0]["messageSummary"] == "DEPENDENCY_ANALYSIS request summary."
    assert "Show dependency information" not in str(history["historyLookup"])
    assert len(run_repository.list_codex_runs()) == 1
    assert artifact_repository.list_all() == []
    assert approval_repository.list_all() == []


def test_codex_runner_intent_submits_schema_aware_runtime_request_metadata_only():
    _clear_repositories()

    response = chat_service.create_chat_run(
        "Analyze PPM.dbo.InvoiceAudit procedure",
        actor_id="analyst-1",
    )

    assert response["status"] == "ACCEPTED"
    assert response["intent"] == "SP_ANALYSIS"
    assert response["route"] == "codex_runner"
    assert response["fakeRunner"] == {"status": "SUCCEEDED", "proposalCount": 1}

    codex_run = run_repository.get_codex_run(response["codexRunId"])
    assert codex_run["run_type"] == "SP_ANALYSIS"
    assert codex_run["output_schema_name"] == "schemas/sp_analysis_result.schema.json"
    assert codex_run["skill_allowlist"] == [
        "runtime-sp-analysis",
        "runtime-output-validation",
        "runtime-policy-review",
    ]
    assert codex_run["tool_mode"] == "EVIDENCE_BUNDLE_ONLY"
    assert codex_run["target_key"] == "PPM.PROCEDURE.dbo.InvoiceAudit"
    assert codex_run["target_object_type"] == "PROCEDURE"
    assert codex_run["target_schema"] == "dbo"
    assert codex_run["target_name"] == "InvoiceAudit"
    assert "contentMarkdown" not in str(codex_run)
    assert artifact_repository.list_all() == []
