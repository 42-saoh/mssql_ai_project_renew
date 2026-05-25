from __future__ import annotations

import pytest

from apps.api.api_app.repositories import artifact_repository, validation_repository
from apps.api.api_app.services import artifact_service
from plf_agent_validation.policy_validator import validate_runtime_result
from plf_agent_validation.redaction_validator import find_redaction_violations


def _base_result(artifact: dict | None = None, *, run_type: str = "SP_ANALYSIS") -> dict:
    artifact = artifact or {
        "artifactType": "SP_ANALYSIS_DOC",
        "title": "Analysis",
        "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.1"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
    }
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": run_type,
        "targetKey": "profile.PROCEDURE.dbo.InvoiceAudit",
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [artifact],
        "blockers": [],
        "validation": {
            "schemaValid": True,
            "policyValid": True,
            "staticValidationPassed": True,
        },
    }


def test_runtime_validator_requires_visible_review_marker_in_generated_content():
    result = _base_result()
    result["artifactProposals"][0]["contentMarkdown"] = "Generated proposal."

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "MISSING_REVIEW_MARKER_IN_CONTENT" in blockers


def test_runtime_validator_blocks_unsafe_table_design_preview():
    result = _base_result(
        {
            "artifactType": "TABLE_DESIGN_PREVIEW",
            "title": "Preview",
            "contentMarkdown": "Generated preview. REVIEW_REQUIRED.",
            "evidenceRefs": ["evidence.1"],
            "reviewMarkers": ["REVIEW_REQUIRED"],
            "previewType": "TABLE_DESIGN_PREVIEW",
            "createTableScriptPreview": "CREATE TABLE dbo.X (id int); INSERT dbo.X VALUES (1);",
            "reviewRequired": True,
            "blockedFromAutoApply": False,
        },
        run_type="TABLE_DESIGN",
    )

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "TABLE_DESIGN_PREVIEW_STATIC:INSERT" in blockers
    assert "TABLE_DESIGN_PREVIEW_STATIC:AUTO_APPLY_NOT_BLOCKED" in blockers


def test_runtime_validator_checks_java_mybatis_static_review_markers():
    result = _base_result(
        {
            "artifactType": "DTO_DRAFT",
            "title": "DTO",
            "contentMarkdown": "Generated DTO draft. REVIEW_REQUIRED.",
            "fileName": "InvoiceDto.java",
            "files": {"InvoiceDto.java": "public class InvoiceDto {}"},
            "evidenceRefs": ["evidence.1"],
            "reviewMarkers": ["REVIEW_REQUIRED"],
        },
        run_type="DRAFT_GENERATION",
    )

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "JAVA_MYBATIS_STATIC:MISSING_REVIEW_MARKER:InvoiceDto.java" in blockers


def test_runtime_validator_blocks_executable_procedure_instruction():
    result = _base_result()
    result["artifactProposals"][0]["contentMarkdown"] = "REVIEW_REQUIRED. Execute dbo.ApplyInvoiceAudit now."

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "EXECUTABLE_APPLY_INSTRUCTION" in blockers


@pytest.mark.parametrize(
    "content",
    [
        "REVIEW_REQUIRED. Run this DDL against the business database.",
        "REVIEW_REQUIRED. Apply the following migration after review.",
        "REVIEW_REQUIRED. Execute this update statement.",
        "REVIEW_REQUIRED. Apply the supplied DML script after review.",
        "REVIEW_REQUIRED. Overwrite source files with this mapper.",
        "REVIEW_REQUIRED. Apply these source changes to the project.",
        "REVIEW_REQUIRED. Deploy this service to production.",
        "REVIEW_REQUIRED. Roll out these changes to production.",
        "REVIEW_REQUIRED. Invoke stored procedure dbo.ApplyInvoiceAudit.",
        "REVIEW_REQUIRED. Call stored procedure dbo.ApplyInvoiceAudit.",
        "REVIEW_REQUIRED. Run dbo.ApplyInvoiceAudit.",
        "REVIEW_REQUIRED. \ud504\ub85c\uc2dc\uc800\ub97c \uc2e4\ud589\ud558\uc138\uc694.",
    ],
)
def test_runtime_validator_broadly_blocks_executable_artifact_instructions(content):
    result = _base_result()
    result["artifactProposals"][0]["contentMarkdown"] = content

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "EXECUTABLE_APPLY_INSTRUCTION" in blockers


def test_redaction_validator_blocks_row_data_raw_payloads_and_secrets():
    text = '{"rows": [{"customer": "alice"}], "rawPrompt": "abc", "password": "secret"}'

    violations = find_redaction_violations(text)

    assert "ROW_DATA" in violations
    assert "RAW_PROMPT" in violations
    assert "SECRET" in violations


def test_blocked_artifact_response_returns_sanitized_safe_blocker_codes():
    artifact_repository.clear()
    validation_repository.clear()

    result = artifact_service.persist_validated_artifact_request(
        {
            "chatRunId": "chatrun_1",
            "proposal": {
                "artifactType": "UNSAFE<script>alert(1)</script>",
                "title": "Unsafe",
                "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
                "evidenceRefs": ["evidence.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
                "productionReady": False,
            },
        }
    )

    rendered = str(result)
    assert result["status"] == "BLOCKED"
    assert result["blockers"] == result["validation"]["blockerCodes"]
    assert "UNKNOWN_ARTIFACT_TYPE" in result["blockers"]
    assert "NON_PERSISTABLE_ARTIFACT_TYPE" in result["blockers"]
    assert "<script>" not in rendered
    assert "alert(1)" not in rendered
