import pytest
import plf_agent_orchestration.graph as graph_module

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    observability_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import artifact_service, chat_service
from apps.api.api_app.services.observability_service import (
    ObservabilityEventError,
    build_observability_event,
    record_observability_event,
)


class _BlockedPgpt:
    def __init__(self):
        self.settings = type("Settings", (), {"model": "test-pgpt"})()
        self.calls: list[str] = []

    def classify_message(self, message: str):
        self.calls.append(message)
        raise AssertionError("PGPT must not be called for redaction-blocked chat input")


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()
    observability_repository.clear()


@pytest.mark.parametrize(
    ("message", "expected_blocker", "unsafe_fragments"),
    [
        (
            "Analyze PPM.dbo.InvoiceAudit procedure with password=abc",
            "SECRET",
            ["password=abc"],
        ),
        (
            "Analyze PPM.dbo.InvoiceAudit procedure and include raw prompt",
            "RAW_PROMPT",
            ["raw prompt"],
        ),
        (
            "Analyze PPM.dbo.InvoiceAudit procedure and include raw provider response",
            "RAW_PROVIDER_RESPONSE",
            ["raw provider response"],
        ),
        (
            "Analyze PPM.dbo.InvoiceAudit procedure using Server=tcp:prod;Database=ERP;Integrated Security=True;",
            "CONNECTION_STRING",
            ["Server=tcp:prod", "Database=ERP", "Integrated Security=True"],
        ),
    ],
)
def test_g11_redaction_markers_hard_block_before_downstream_side_effects(
    monkeypatch, message, expected_blocker, unsafe_fragments
):
    _clear_repositories()
    pgpt = _BlockedPgpt()
    calls = {"metadata": 0, "runner": 0}

    def fail_metadata(*_args, **_kwargs):
        calls["metadata"] += 1
        raise AssertionError("Metadata gateway must not be called for redaction-blocked chat input")

    def fail_runner(*_args, **_kwargs):
        calls["runner"] += 1
        raise AssertionError("Codex Runner must not be called for redaction-blocked chat input")

    def fail_orchestrator(*_args, **_kwargs):
        raise AssertionError("Orchestrator routing must not be called for redaction-blocked chat input")

    monkeypatch.setattr(chat_service, "orchestrate_message", fail_orchestrator)
    monkeypatch.setattr(graph_module.PgptResponsesClient, "from_env", staticmethod(lambda: pgpt))
    monkeypatch.setattr(chat_service.metadata_service, "search_metadata", fail_metadata)
    monkeypatch.setattr(chat_service, "submit_codex_run", fail_runner)

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert expected_blocker in response["blockers"]
    assert response["checkpoint"]["blockers"] == ["REDACTION_VIOLATION_BLOCKED"]
    assert response["orchestrator"]["nodes"] == ["pre_route_redaction_gate"]
    assert "approvalId" not in response
    assert "codexRunId" not in response
    assert "metadataSearch" not in response
    assert "fakeRunner" not in response
    assert calls == {"metadata": 0, "runner": 0}
    assert pgpt.calls == []
    assert approval_repository.list_all() == []
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []

    stored_run = run_repository.get_chat_run(response["chatRunId"])
    assert stored_run["blockers"] == ["REDACTION_VIOLATION_BLOCKED"]
    events = observability_repository.list_all()
    assert [event["event_type"] for event in events] == ["chat_run_recorded"]
    assert events[0]["blocker_codes"] == ["REDACTION_VIOLATION_BLOCKED"]

    persisted_rendered = str(
        [
            conversation_repository.list_all(),
            run_repository.list_chat_runs(),
            observability_repository.list_all(),
        ]
    )
    for fragment in unsafe_fragments:
        assert fragment.lower() not in persisted_rendered.lower()


def test_blocked_request_observability_is_sanitized_and_has_no_side_effects():
    _clear_repositories()
    raw_message = "exec dbo.ProcessOrder password=abc"

    response = chat_service.create_chat_run(raw_message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in response["blockers"]
    assert approval_repository.list_all() == []
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []

    events = observability_repository.list_all()
    assert [event["event_type"] for event in events] == ["chat_run_recorded"]
    rendered_events = str(events)
    assert raw_message not in rendered_events
    assert "password=abc" not in rendered_events
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in rendered_events


def test_unsafe_artifact_validation_observability_uses_sanitized_blocker_codes():
    _clear_repositories()

    result = artifact_service.persist_artifact_after_validation(
        {
            "artifactType": "SP_ANALYSIS_DOC",
            "title": "Unsafe",
            "contentMarkdown": "REVIEW_REQUIRED\nraw prompt: password=abc",
            "evidenceRefs": ["evidence.1"],
            "reviewMarkers": ["REVIEW_REQUIRED"],
            "productionReady": False,
        },
        chat_run_id="chatrun_1",
    )

    assert result["status"] == "BLOCKED"
    assert artifact_repository.list_all() == []
    assert "RAW_PROMPT" in result["blockers"]

    events = observability_repository.list_all()
    assert [event["event_type"] for event in events] == ["artifact_validation_blocked"]
    assert events[0]["blocker_codes"] == ["REDACTION_VIOLATION_BLOCKED"]
    rendered_events = str(events).lower()
    assert "raw prompt" not in rendered_events
    assert "password=abc" not in rendered_events
    assert "raw_prompt" not in rendered_events


def test_observability_event_rejects_unsupported_raw_fields():
    _clear_repositories()

    with pytest.raises(ObservabilityEventError):
        record_observability_event(
            "chat_run_recorded",
            subject_type="chat_run",
            subject_id="chatrun_unsafe",
            raw_prompt="show table data",
        )

    assert observability_repository.list_all() == []


def test_observability_blocker_sanitization_blocks_redaction_codes():
    event = build_observability_event(
        "artifact_validation_blocked",
        subject_type="artifact_validation",
        subject_id="validation_1",
        blocker_codes=["RAW_PROMPT", "password=abc", "SAFE_POLICY_CODE"],
    )

    assert event["blocker_codes"] == ["REDACTION_VIOLATION_BLOCKED", "SAFE_POLICY_CODE"]
