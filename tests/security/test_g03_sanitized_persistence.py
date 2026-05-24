from apps.api.api_app.repositories import artifact_repository, conversation_repository, run_repository, validation_repository
from apps.api.api_app.services import artifact_service, chat_service


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()


def test_raw_user_message_is_not_persisted_in_chat_storage():
    _clear_repositories()
    raw_message = "Show dependency information for table password:abc"

    response = chat_service.create_chat_run(raw_message, actor_id="analyst-1")

    stored_text = str(conversation_repository.list_all()) + str(run_repository.list_chat_runs())
    assert raw_message not in stored_text
    assert "password:abc" not in stored_text
    assert response["status"] in {"ACCEPTED", "BLOCKED"}


def test_raw_or_executable_artifact_payload_is_not_persisted():
    _clear_repositories()
    result = artifact_service.persist_artifact_after_validation(
        {
            "artifactType": "SP_ANALYSIS_DOC",
            "title": "Unsafe",
            "contentMarkdown": "raw prompt: apply this ddl",
            "evidenceRefs": ["evidence.1"],
            "reviewMarkers": ["REVIEW_REQUIRED"],
            "productionReady": False,
        },
        chat_run_id="chatrun_1",
    )

    assert result["status"] == "BLOCKED"
    assert artifact_repository.list_all() == []
    assert "raw prompt" not in str(validation_repository.list_all()).lower()
