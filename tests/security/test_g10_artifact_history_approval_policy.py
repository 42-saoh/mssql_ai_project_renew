from __future__ import annotations

from pathlib import Path

import yaml

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import approval_service, artifact_service, chat_service

ROOT = Path(__file__).resolve().parents[2]


def _clear_repositories() -> None:
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_g10_raw_payload_artifact_attempt_persists_only_safe_blocker_codes():
    _clear_repositories()

    result = artifact_service.persist_validated_artifact_request(
        {
            "chatRunId": "chatrun_1",
            "proposal": {
                "artifactType": "SP_ANALYSIS_DOC",
                "title": "Unsafe",
                "contentMarkdown": "raw prompt REVIEW_REQUIRED",
                "evidenceRefs": ["evidence.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
                "productionReady": False,
            },
        }
    )

    persisted = str(validation_repository.list_all()).lower()
    assert result["status"] == "BLOCKED"
    assert artifact_repository.list_all() == []
    assert "raw prompt" not in persisted
    assert "raw_prompt" not in persisted
    assert "REDACTION_VIOLATION_BLOCKED" in validation_repository.list_all()[0]["blocker_codes"]


def test_g10_approval_resume_does_not_cross_execution_or_persistence_boundaries():
    _clear_repositories()

    blocked = chat_service.create_chat_run("Please apply this DDL", actor_id="analyst-1")
    before_chat_runs = run_repository.list_chat_runs()

    resumed = approval_service.resume_approval(blocked["approvalId"])

    assert resumed["status"] == "RESUMED"
    assert run_repository.list_chat_runs() == before_chat_runs
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []


def test_g10_streamlit_review_pages_remain_fastapi_only_and_avoid_unsafe_labels():
    spec = yaml.safe_load(
        (ROOT / "spec/development/artifact_history_approval_ux_completion.yaml").read_text(
            encoding="utf-8"
        )
    )
    text = "\n".join(
        _read(path)
        for path in [
            spec["uiCompletion"]["apiClientPath"],
            *(page["path"] for page in spec["uiCompletion"]["pages"].values()),
        ]
    )

    assert "ApiClient(" in text
    assert "mssql_mcp" not in text
    assert "runner_app" not in text
    assert "sqlalchemy" not in text
    for label in spec["uiCompletion"]["forbiddenUnsafeLabels"]:
        assert label not in text
