import pytest

from apps.api.api_app.repositories import artifact_repository, validation_repository
from apps.api.api_app.services import artifact_service


def _clear_repositories():
    artifact_repository.clear()
    validation_repository.clear()


def _valid_proposal() -> dict:
    return {
        "artifactType": "SP_ANALYSIS_DOC",
        "title": "Analysis",
        "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
        "productionReady": False,
    }


@pytest.mark.parametrize(
    ("field", "missing_blocker"),
    [
        ("evidenceRefs", "MISSING_EVIDENCE_REFS"),
        ("reviewMarkers", "MISSING_REVIEW_MARKERS"),
    ],
)
def test_artifact_persistence_blocks_missing_required_schema_arrays(field: str, missing_blocker: str):
    _clear_repositories()
    proposal = _valid_proposal()
    proposal.pop(field)

    result = artifact_service.persist_artifact_after_validation(proposal, chat_run_id="chatrun_1")

    assert result["status"] == "BLOCKED"
    assert missing_blocker in result["blockers"]
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and field in blocker for blocker in result["blockers"])
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and field in blocker for blocker in result["blockers"])
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all()[0]["schema_valid"] is False


@pytest.mark.parametrize(
    ("field", "missing_blocker"),
    [
        ("evidenceRefs", "MISSING_EVIDENCE_REFS"),
        ("reviewMarkers", "MISSING_REVIEW_MARKERS"),
    ],
)
def test_artifact_persistence_blocks_empty_required_schema_arrays(field: str, missing_blocker: str):
    _clear_repositories()
    proposal = _valid_proposal()
    proposal[field] = []

    result = artifact_service.persist_artifact_after_validation(proposal, chat_run_id="chatrun_1")

    assert result["status"] == "BLOCKED"
    assert missing_blocker in result["blockers"]
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and field in blocker for blocker in result["blockers"])
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and field in blocker for blocker in result["blockers"])
    assert artifact_repository.list_all() == []
    assert validation_repository.list_all()[0]["schema_valid"] is False
