from __future__ import annotations

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


def test_redaction_validator_blocks_row_data_raw_payloads_and_secrets():
    text = '{"rows": [{"customer": "alice"}], "rawPrompt": "abc", "password": "secret"}'

    violations = find_redaction_violations(text)

    assert "ROW_DATA" in violations
    assert "RAW_PROMPT" in violations
    assert "SECRET" in violations
