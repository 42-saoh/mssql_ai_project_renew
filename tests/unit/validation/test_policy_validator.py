from plf_agent_validation.policy_validator import validate_runtime_result


def test_valid_runtime_result_passes():
    result = {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": "SP_ANALYSIS",
        "targetKey": "ppm.PROCEDURE.dbo.X",
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [
            {
                "artifactType": "SP_ANALYSIS_DOC",
                "title": "Analysis",
                "contentMarkdown": "REVIEW_REQUIRED",
                "evidenceRefs": ["evidence.1"],
                "reviewMarkers": ["REVIEW_REQUIRED"],
            }
        ],
        "blockers": [],
        "validation": {},
    }
    ok, blockers = validate_runtime_result(result)
    assert ok, blockers


def test_production_ready_is_blocked():
    ok, blockers = validate_runtime_result({"productionReady": True, "artifactProposals": []})
    assert not ok
    assert "PRODUCTION_READY_TRUE_BLOCKED" in blockers


def test_retired_artifact_type_is_blocked():
    ok, blockers = validate_runtime_result({"productionReady": False, "artifactProposals": [{"artifactType": "DDL_DRAFT", "reviewMarkers": ["REVIEW_REQUIRED"]}]})
    assert not ok
    assert any("DDL_DRAFT" in blocker for blocker in blockers)
