from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from plf_agent_validation.policy_validator import validate_runtime_result
from runner_app.validator import validation_flags

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel_path: str) -> dict:
    return yaml.safe_load((ROOT / rel_path).read_text(encoding="utf-8"))


def _result(content: str) -> dict:
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": "SP_ANALYSIS",
        "targetKey": "profile.PROCEDURE.dbo.InvoiceAudit",
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [
            {
                "artifactType": "SP_ANALYSIS_DOC",
                "title": "Analysis",
                "contentMarkdown": content,
                "evidenceRefs": ["evidence.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
            }
        ],
        "blockers": [],
        "validation": {"schemaValid": True, "policyValid": True, "staticValidationPassed": True},
    }


def test_g08_runtime_output_validation_eval_cases_are_declared():
    eval_spec = _load_yaml("spec/eval/v2_runtime_output_validation.yaml")
    case_ids = {case["id"] for case in eval_spec["cases"]}

    assert "g08_runtime_skills_declare_run_scope_schema_and_artifact_types" in case_ids
    assert "g08_requested_output_schema_mismatch_returns_blocked_result" in case_ids
    assert "g08_static_and_redaction_validators_block_unsafe_outputs" in case_ids


def test_g08_eval_runtime_schema_mismatch_is_a_schema_blocker():
    result = _result("Generated proposal. REVIEW_REQUIRED.")
    result["artifactProposals"][0]["artifactType"] = "DEPENDENCY_REPORT"

    flags, blockers = validation_flags(result, output_schema="schemas/sp_analysis_result.schema.json")

    assert flags["schemaValid"] is False
    assert any("RUNTIME_OUTPUT_SCHEMA_INVALID" in blocker for blocker in blockers)


@pytest.mark.parametrize(
    ("content", "expected_blocker"),
    [
        ("Generated proposal without visible marker.", "MISSING_REVIEW_MARKER_IN_CONTENT"),
        ("REVIEW_REQUIRED. Execute this SQL against production.", "EXECUTABLE_APPLY_INSTRUCTION"),
        ("REVIEW_REQUIRED. raw provider response: secret model text", "RAW_PROVIDER_RESPONSE"),
        ("REVIEW_REQUIRED. sample data: customer alice", "ROW_DATA"),
    ],
)
def test_g08_eval_policy_and_redaction_block_unsafe_outputs(content, expected_blocker):
    ok, blockers = validate_runtime_result(_result(content))

    assert not ok
    assert expected_blocker in blockers
