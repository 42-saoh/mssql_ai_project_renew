from __future__ import annotations

import json
import subprocess
from pathlib import Path

from runner_app.real_runner import RealRunnerConfig, submit_real_run
from runner_app.validator import validation_flags

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_TEMPLATE = ROOT / "services/codex-runner/runtime-template"


def _request(output_schema: str = "sp_analysis_result.schema.json") -> dict:
    return {
        "schemaVersion": "ServiceCodexRunRequest.v1",
        "runType": "SP_ANALYSIS",
        "chatRunId": "chat-1",
        "conversationId": "conv-1",
        "target": {
            "dbProfileId": "profile-1",
            "objectType": "PROCEDURE",
            "schema": "dbo",
            "name": "InvoiceAudit",
            "targetKey": "profile-1.PROCEDURE.dbo.InvoiceAudit",
        },
        "policy": {
            "allowRowData": False,
            "allowProcedureExecution": False,
            "allowDdlDmlApply": False,
            "allowSourceApply": False,
            "allowDeploy": False,
            "allowRawPromptStorage": False,
            "allowRawProviderResponseStorage": False,
        },
        "toolMode": "EVIDENCE_BUNDLE_ONLY",
        "skillAllowlist": ["runtime-sp-analysis", "runtime-output-validation", "runtime-policy-review"],
        "outputSchema": output_schema,
        "evidenceBundleRef": "evidence.bundle.1",
    }


def _sp_result(*, artifact_type: str = "SP_ANALYSIS_DOC", run_type: str = "SP_ANALYSIS") -> dict:
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": run_type,
        "targetKey": "profile-1.PROCEDURE.dbo.InvoiceAudit",
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [
            {
                "artifactType": artifact_type,
                "title": "Invoice audit proposal",
                "contentMarkdown": "Generated proposal. REVIEW_REQUIRED.",
                "evidenceRefs": ["evidence.bundle.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
            }
        ],
        "blockers": [],
        "validation": {"schemaValid": True, "policyValid": True, "staticValidationPassed": True},
    }


def test_requested_runtime_output_schema_is_validated_after_generic_schema():
    result = _sp_result(artifact_type="DEPENDENCY_REPORT")

    flags, blockers = validation_flags(result, output_schema="schemas/sp_analysis_result.schema.json")

    assert flags["schemaValid"] is False
    assert flags["policyValid"] is True
    assert flags["staticValidationPassed"] is False
    assert any("RUNTIME_OUTPUT_SCHEMA_INVALID" in blocker and "artifactType" in blocker for blocker in blockers)


def test_submit_real_run_blocks_generic_valid_result_that_violates_requested_runtime_schema(tmp_path):
    def fake_codex(command, **kwargs):
        workspace = Path(command[command.index("--cd") + 1])
        assert command[command.index("--output-schema") + 1] == "schemas/sp_analysis_result.schema.json"
        (workspace / "outputs/final.json").write_text(
            json.dumps(_sp_result(artifact_type="DEPENDENCY_REPORT")),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = submit_real_run(
        _request(),
        {"evidenceRefs": ["evidence.bundle.1"]},
        config=RealRunnerConfig(workspace_base=tmp_path, runtime_template=RUNTIME_TEMPLATE),
        run_command=fake_codex,
    )

    assert result["status"] == "BLOCKED"
    assert result["artifactProposals"] == []
    assert result["validation"]["schemaValid"] is False
    assert result["validation"]["policyValid"] is True
    assert any("RUNTIME_OUTPUT_SCHEMA_INVALID" in blocker for blocker in result["blockers"])


def test_requested_runtime_schema_accepts_matching_result():
    flags, blockers = validation_flags(_sp_result(), output_schema="sp_analysis_result.schema.json")

    assert flags == {"schemaValid": True, "policyValid": True, "staticValidationPassed": True}
    assert blockers == []
