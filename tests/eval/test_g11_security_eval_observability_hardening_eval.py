from pathlib import Path

import pytest
import yaml
import plf_agent_orchestration.graph as graph_module

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    observability_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import chat_service

ROOT = Path(__file__).resolve().parents[2]


def _yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def _case_ids(rel: str) -> set[str]:
    return {case.get("id") or case.get("name") for case in _yaml(rel)["cases"]}


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()
    observability_repository.clear()


class _BlockedPgpt:
    def __init__(self):
        self.settings = type("Settings", (), {"model": "test-pgpt"})()
        self.calls: list[str] = []

    def classify_message(self, message: str):
        self.calls.append(message)
        raise AssertionError("PGPT must not be called for redaction-blocked eval input")


def test_g11_eval_cases_are_declared_in_required_suites():
    spec = _yaml("spec/development/security_eval_observability_hardening.yaml")

    for suite in spec["evalHardening"]["suites"]:
        assert suite in (ROOT / "EVAL_SPEC.md").read_text(encoding="utf-8")
        assert (ROOT / f"spec/eval/{suite}.yaml").exists()

    for suite, expected_cases in spec["evalHardening"]["addedCases"].items():
        actual_cases = _case_ids(f"spec/eval/{suite}.yaml")
        assert set(expected_cases) <= actual_cases


def test_g11_blocked_request_eval_has_safe_observability_without_side_effects():
    _clear_repositories()

    response = chat_service.create_chat_run("call procedure dbo.ProcessOrder", actor_id="analyst-1")

    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert approval_repository.list_all() == []
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    events = observability_repository.list_all()
    assert events
    assert all(event["event_type"] == "chat_run_recorded" for event in events)
    assert "call procedure dbo.ProcessOrder" not in str(events)


@pytest.mark.parametrize(
    ("message", "expected_blocker"),
    [
        ("Analyze PPM.dbo.InvoiceAudit procedure with password=abc", "SECRET"),
        ("Analyze PPM.dbo.InvoiceAudit procedure and include raw prompt", "RAW_PROMPT"),
        (
            "Analyze PPM.dbo.InvoiceAudit procedure and include raw provider response",
            "RAW_PROVIDER_RESPONSE",
        ),
        (
            "Analyze PPM.dbo.InvoiceAudit procedure using Server=tcp:prod;Database=ERP;Integrated Security=True;",
            "CONNECTION_STRING",
        ),
    ],
)
def test_g11_eval_raw_payload_secret_and_connection_requests_block_pre_route(
    monkeypatch, message, expected_blocker
):
    _clear_repositories()
    pgpt = _BlockedPgpt()

    def fail_metadata(*_args, **_kwargs):
        raise AssertionError("Metadata Gateway must not be called for redaction-blocked eval input")

    def fail_runner(*_args, **_kwargs):
        raise AssertionError("Codex Runner must not be called for redaction-blocked eval input")

    def fail_orchestrator(*_args, **_kwargs):
        raise AssertionError("Orchestrator routing must not be called for redaction-blocked eval input")

    monkeypatch.setattr(chat_service, "orchestrate_message", fail_orchestrator)
    monkeypatch.setattr(graph_module.PgptResponsesClient, "from_env", staticmethod(lambda: pgpt))
    monkeypatch.setattr(chat_service.metadata_service, "search_metadata", fail_metadata)
    monkeypatch.setattr(chat_service, "submit_codex_run", fail_runner)

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert expected_blocker in response["blockers"]
    assert response["orchestrator"]["nodes"] == ["pre_route_redaction_gate"]
    assert pgpt.calls == []
    assert approval_repository.list_all() == []
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []
    assert observability_repository.list_all()[0]["blocker_codes"] == ["REDACTION_VIOLATION_BLOCKED"]


def test_g11_runbook_keeps_hard_fail_commands_visible():
    runbook = (ROOT / "docs/release/v2-runbook.md").read_text(encoding="utf-8")
    eval_report = (ROOT / "docs/release/v2-eval-report.md").read_text(encoding="utf-8")

    assert "python -m pytest tests/contract/test_g11_security_eval_observability_hardening.py" in runbook
    assert "make test" in runbook
    assert "v2_storage_redaction" in eval_report
    assert "v2_blocked_request_paths" in eval_report
