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


def _valid_proposal() -> dict:
    return {
        "artifactType": "SERVICE_DRAFT",
        "title": "Service draft",
        "contentMarkdown": "Generated Java service draft. REVIEW_REQUIRED.",
        "className": "OrderService",
        "filePath": "src/main/java/com/example/OrderService.java",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }


def test_g10_eval_cases_are_declared():
    eval_spec = yaml.safe_load(
        (ROOT / "spec/eval/v2_artifact_history_approval_ux.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert eval_spec["name"] == "v2_artifact_history_approval_ux"
    assert eval_spec["suite"] == "v2_artifact_history_approval_ux"
    assert {
        "g10_validated_artifact_persistence_records_validation_metadata",
        "g10_invalid_or_preview_artifacts_block_before_persistence",
        "g10_history_returns_sanitized_summaries_only",
        "g10_approval_resume_has_no_execution_side_effects",
        "g10_streamlit_review_ux_uses_fastapi_client_only",
    } <= {case["id"] for case in eval_spec["cases"]}


def test_g10_eval_valid_artifact_history_and_approval_paths_are_safe():
    _clear_repositories()

    artifact_result = artifact_service.persist_validated_artifact_request(
        {
            "chatRunId": "chatrun_eval",
            "codexRunId": "codexrun_eval",
            "proposal": _valid_proposal(),
        }
    )
    chat_service.create_chat_run(
        "Show dependency information for dbo.Orders",
        conversation_id="conv_eval",
        actor_id="analyst-1",
    )
    blocked = chat_service.create_chat_run("Please apply this DDL", actor_id="analyst-1")
    resumed = approval_service.resume_approval(blocked["approvalId"])

    rendered_history = str(chat_service.get_conversation("conv_eval"))

    assert artifact_result["status"] == "PERSISTED"
    assert artifact_result["artifact"]["validationStatus"] == "VALIDATED"
    assert "contentMarkdown" not in str(artifact_result["artifact"])
    assert "Show dependency information" not in rendered_history
    assert "dbo.Orders" not in rendered_history
    assert resumed == {"approvalId": blocked["approvalId"], "status": "RESUMED"}
    assert len(run_repository.list_codex_runs()) == 1
    assert len(artifact_repository.list_all()) == 1
