from __future__ import annotations

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    observability_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import approval_service, artifact_service, chat_service


def _clear_repositories() -> None:
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()
    observability_repository.clear()


def _valid_sp_analysis_proposal() -> dict:
    return {
        "artifactType": "SP_ANALYSIS_DOC",
        "title": "Invoice audit analysis",
        "contentMarkdown": "Generated analysis summary. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.invoice_audit.metadata"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }


def test_g12_codex_runner_proposal_to_validated_artifact_review_flow():
    _clear_repositories()

    response = chat_service.create_chat_run(
        "Analyze PPM.dbo.InvoiceAudit procedure",
        actor_id="analyst-1",
    )

    assert response["status"] == "ACCEPTED"
    assert response["intent"] == "SP_ANALYSIS"
    assert response["route"] == "codex_runner"
    assert response["fakeRunner"] == {"status": "SUCCEEDED", "proposalCount": 1}
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []

    codex_run = run_repository.get_codex_run(response["codexRunId"])
    assert codex_run is not None
    assert codex_run["runner_mode"] == "fake"
    assert codex_run["status"] == "SUBMITTED"
    assert codex_run["validation_status"] == "PENDING"
    assert codex_run["output_schema_name"] == "schemas/sp_analysis_result.schema.json"
    assert "contentMarkdown" not in str(codex_run)

    persisted = artifact_service.persist_validated_artifact_request(
        {
            "chatRunId": response["chatRunId"],
            "codexRunId": response["codexRunId"],
            "proposal": _valid_sp_analysis_proposal(),
        }
    )

    assert persisted["status"] == "PERSISTED"
    artifact = persisted["artifact"]
    assert artifact["artifactType"] == "SP_ANALYSIS_DOC"
    assert artifact["productionReady"] is False
    assert artifact["reviewRequired"] is True
    assert artifact["validationStatus"] == "VALIDATED"
    assert artifact["reviewMarkers"] == ["REVIEW_REQUIRED"]
    assert "contentMarkdown" not in str(artifact)
    assert "Generated analysis summary" not in str(artifact_repository.list_all())
    assert {event["event_type"] for event in observability_repository.list_all()} >= {
        "chat_run_recorded",
        "codex_run_submitted",
        "artifact_persisted",
    }


def test_g12_metadata_search_and_history_lookup_stay_sanitized(monkeypatch):
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

    metadata = chat_service.create_chat_run(
        "Find order table metadata",
        conversation_id="conv_g12",
        actor_id="analyst-1",
    )
    history = chat_service.create_chat_run(
        "show history",
        conversation_id="conv_g12",
        actor_id="analyst-1",
    )

    assert metadata["status"] == "ACCEPTED"
    assert metadata["route"] == "metadata_gateway"
    assert metadata["metadataSearch"]["toolName"] == "search_metadata_objects"
    assert captured == {
        "query": "Find order table metadata",
        "db_profile_id": "master",
        "object_types": None,
        "limit": 20,
    }
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert approval_repository.list_all() == []

    assert history["status"] == "ACCEPTED"
    assert history["route"] == "history_store"
    assert history["historyLookup"]["items"][0]["messageSummary"] == "Metadata search request summary."
    rendered_history = str(history["historyLookup"])
    assert "Find order table metadata" not in rendered_history
    assert "TB_ORDER" not in str(run_repository.list_chat_runs())


def test_g12_approval_resume_is_review_metadata_only():
    _clear_repositories()

    response = chat_service.create_chat_run("Please apply this DDL", actor_id="analyst-1")
    before_runs = run_repository.list_chat_runs()

    resumed = approval_service.resume_approval(response["approvalId"])

    assert response["policyDecision"] == "BLOCKED_OR_APPROVAL_REQUIRED"
    assert response["route"] == "blocked"
    assert resumed == {"approvalId": response["approvalId"], "status": "RESUMED"}
    assert run_repository.list_chat_runs() == before_runs
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []


def test_g12_stored_procedure_execution_is_hard_blocked_without_side_effects():
    _clear_repositories()

    response = chat_service.create_chat_run("exec dbo.ProcessOrder", actor_id="analyst-1")

    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in response["blockers"]
    assert response["pgptUsed"] is False
    assert run_repository.list_codex_runs() == []
    assert approval_repository.list_all() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []
