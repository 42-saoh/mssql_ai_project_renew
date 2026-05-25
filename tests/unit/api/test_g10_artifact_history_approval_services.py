from __future__ import annotations

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
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


def _valid_proposal() -> dict:
    return {
        "artifactType": "SP_ANALYSIS_DOC",
        "title": "Analysis",
        "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }


def test_g10_artifact_detail_exposes_validation_metadata_without_inline_content():
    _clear_repositories()

    persisted = artifact_service.persist_validated_artifact_request(
        {
            "chatRunId": "chatrun_1",
            "codexRunId": "codexrun_1",
            "proposal": _valid_proposal(),
        }
    )

    assert persisted["status"] == "PERSISTED"
    artifact_id = persisted["artifact"]["artifactId"]
    detail = artifact_service.get_artifact(artifact_id)
    validations = artifact_service.list_artifact_validations(artifact_id)

    assert detail["productionReady"] is False
    assert detail["reviewRequired"] is True
    assert detail["contentRef"].startswith("memory://artifacts/")
    assert "contentMarkdown" not in str(detail)
    assert detail["validationStatus"] == "VALIDATED"
    assert detail["validation"]["policyValid"] is True
    assert validations["items"][0]["validationId"] == persisted["validation"]["validationId"]


def test_g10_invalid_or_preview_artifacts_block_before_persistence():
    _clear_repositories()
    proposal = _valid_proposal()
    proposal["artifactType"] = "TABLE_DESIGN_PREVIEW"

    result = artifact_service.persist_validated_artifact_request(
        {"chatRunId": "chatrun_1", "proposal": proposal}
    )

    assert result["status"] == "BLOCKED"
    assert "NON_PERSISTABLE_ARTIFACT_TYPE:TABLE_DESIGN_PREVIEW" in result["blockers"]
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all()[0]["artifact_id"] == ""


def test_g10_history_lists_sanitized_conversation_summaries_only():
    _clear_repositories()

    response = chat_service.create_chat_run(
        "Show dependency information for dbo.Orders",
        conversation_id="conv_g10",
        actor_id="analyst-1",
    )

    assert response["status"] == "ACCEPTED"
    conversations = chat_service.list_conversations()
    detail = chat_service.get_conversation("conv_g10")
    rendered = str({"list": conversations, "detail": detail})

    assert conversations["items"][0]["conversationId"] == "conv_g10"
    assert conversations["items"][0]["runCount"] == 1
    assert detail["items"][0]["messageSummary"] == "DEPENDENCY_ANALYSIS request summary."
    assert "Show dependency information" not in rendered
    assert "dbo.Orders" not in rendered
    assert "raw prompt" not in rendered.lower()
    assert "provider response" not in rendered.lower()


def test_g10_approval_resume_updates_review_metadata_without_side_effects():
    _clear_repositories()

    blocked = chat_service.create_chat_run("Please apply this DDL", actor_id="analyst-1")
    approval_id = blocked["approvalId"]

    approvals = approval_service.list_approvals()
    approval = approval_service.get_approval(approval_id)
    resumed = approval_service.resume_approval(approval_id)

    assert approvals["items"][0]["approvalId"] == approval_id
    assert approval["status"] == "PENDING"
    assert resumed == {"approvalId": approval_id, "status": "RESUMED"}
    assert approval_service.get_approval(approval_id)["status"] == "RESUMED"
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all() == []
