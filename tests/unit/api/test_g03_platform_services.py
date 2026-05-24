from apps.api.api_app.repositories import approval_repository, artifact_repository, conversation_repository, run_repository, validation_repository
from apps.api.api_app.services import approval_service, artifact_service, chat_service


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


def test_chat_service_persists_sanitized_run_and_codex_gateway_record():
    _clear_repositories()

    response = chat_service.create_chat_run(
        "Show dependency information for the order table",
        actor_id="analyst-1",
    )

    assert response["status"] == "ACCEPTED"
    assert response["route"] == "codex_runner"
    assert "codexRunId" in response

    stored = run_repository.get_chat_run(response["chatRunId"])
    assert stored is not None
    assert stored["user_message_summary"] == "DEPENDENCY_ANALYSIS request summary."
    assert "Show dependency information" not in str(stored)
    assert run_repository.get_codex_run(response["codexRunId"])["status"] == "SUBMITTED"


def test_blocked_chat_persists_no_codex_run_and_can_create_approval():
    _clear_repositories()

    response = chat_service.create_chat_run("Please apply this DDL", actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED_OR_APPROVAL_REQUIRED"
    assert "codexRunId" not in response
    assert response["approvalId"].startswith("approval_")
    assert run_repository.list_codex_runs() == []

    approval = approval_repository.get(response["approvalId"])
    assert approval["status"] == "PENDING"
    assert approval_service.resume_approval(response["approvalId"])["status"] == "RESUMED"


def test_artifact_service_persists_only_after_validation_and_without_inline_content():
    _clear_repositories()
    proposal = {
        "artifactType": "SP_ANALYSIS_DOC",
        "title": "Analysis",
        "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }

    result = artifact_service.persist_artifact_after_validation(proposal, chat_run_id="chatrun_1")

    assert result["status"] == "PERSISTED"
    artifact = artifact_repository.get(result["artifact"]["artifactId"])
    assert artifact["production_ready"] is False
    assert artifact["review_required"] is True
    assert artifact["content_ref"].startswith("memory://artifacts/")
    assert "contentMarkdown" not in artifact
    assert validation_repository.list_for_artifact(artifact["artifact_id"])[0]["policy_valid"] is True


def test_artifact_service_blocks_invalid_or_production_ready_artifacts():
    _clear_repositories()
    proposal = {
        "artifactType": "DDL_DRAFT",
        "title": "Unsafe",
        "contentMarkdown": "apply this ddl",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": True,
    }

    result = artifact_service.persist_artifact_after_validation(proposal, chat_run_id="chatrun_1")

    assert result["status"] == "BLOCKED"
    assert "PRODUCTION_READY_TRUE_BLOCKED" in result["blockers"]
    assert artifact_repository.list_all() == []
