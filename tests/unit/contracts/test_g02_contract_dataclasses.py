from jsonschema import Draft202012Validator

from plf_agent_contracts.codex_runner import ServiceCodexRunRequest, ServiceCodexRunResult, TargetRef
from plf_agent_contracts.enums import ArtifactType


def test_service_codex_run_request_dataclass_matches_json_schema():
    request = ServiceCodexRunRequest(
        runType="SP_ANALYSIS",
        chatRunId="chatrun_1",
        conversationId="conv_1",
        target=TargetRef(
            dbProfileId="master",
            objectType="PROCEDURE",
            schema="dbo",
            name="X",
            targetKey="master.PROCEDURE.dbo.X",
        ),
        skillAllowlist=["runtime-sp-analysis"],
    )

    schema = {
        "type": "object",
        "required": ["schemaVersion", "runType", "chatRunId", "conversationId", "target", "policy", "toolMode", "skillAllowlist", "outputSchema"],
        "properties": {
            "schemaVersion": {"const": "ServiceCodexRunRequest.v1"},
            "runType": {"enum": ["SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"]},
            "toolMode": {"enum": ["EVIDENCE_BUNDLE_ONLY", "SCOPED_TOOL_PROXY"]},
            "skillAllowlist": {"type": "array", "items": {"type": "string", "pattern": "^runtime-"}},
        },
    }

    Draft202012Validator(schema).validate(request.to_dict())
    assert request.policy["allowRowData"] is False
    assert request.policy["allowProcedureExecution"] is False
    assert request.policy["allowDdlDmlApply"] is False


def test_service_codex_run_result_defaults_are_review_required_and_not_production_ready():
    result = ServiceCodexRunResult(
        runType="SP_ANALYSIS",
        targetKey="master.PROCEDURE.dbo.X",
        status="SUCCEEDED",
        artifactProposals=[
            {
                "artifactType": ArtifactType.SP_ANALYSIS_DOC.value,
                "title": "Analysis",
                "contentMarkdown": "REVIEW_REQUIRED",
                "evidenceRefs": ["evidence.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
            }
        ],
    )

    payload = result.to_dict()
    assert payload["schemaVersion"] == "ServiceCodexRunResult.v1"
    assert payload["productionReady"] is False
    assert payload["reviewRequired"] is True
    assert payload["validation"] == {
        "schemaValid": False,
        "policyValid": False,
        "staticValidationPassed": False,
    }
