from plf_agent_validation.policy_validator import validate_runtime_result


def _valid_runtime_result() -> dict:
    return {
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
        "validation": {
            "schemaValid": True,
            "policyValid": True,
            "staticValidationPassed": True,
        },
    }


def test_valid_runtime_result_passes():
    result = _valid_runtime_result()
    ok, blockers = validate_runtime_result(result)
    assert ok, blockers


def test_production_ready_is_blocked():
    ok, blockers = validate_runtime_result({"productionReady": True, "artifactProposals": []})
    assert not ok
    assert "PRODUCTION_READY_TRUE_BLOCKED" in blockers


def test_retired_artifact_type_is_blocked():
    result = _valid_runtime_result()
    result["artifactProposals"][0]["artifactType"] = "DDL_DRAFT"

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert any("DDL_DRAFT" in blocker for blocker in blockers)


def test_missing_evidence_refs_fails_runner_and_artifact_schema_validation():
    result = _valid_runtime_result()
    result["artifactProposals"][0].pop("evidenceRefs")

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "MISSING_EVIDENCE_REFS" in blockers
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and "evidenceRefs" in blocker for blocker in blockers)
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and "evidenceRefs" in blocker for blocker in blockers)


def test_empty_evidence_refs_fails_runner_and_artifact_schema_validation():
    result = _valid_runtime_result()
    result["artifactProposals"][0]["evidenceRefs"] = []

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "MISSING_EVIDENCE_REFS" in blockers
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and "evidenceRefs" in blocker for blocker in blockers)
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and "evidenceRefs" in blocker for blocker in blockers)


def test_missing_review_markers_fails_runner_and_artifact_schema_validation():
    result = _valid_runtime_result()
    result["artifactProposals"][0].pop("reviewMarkers")

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "MISSING_REVIEW_MARKERS" in blockers
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and "reviewMarkers" in blocker for blocker in blockers)
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and "reviewMarkers" in blocker for blocker in blockers)


def test_empty_review_markers_fails_runner_and_artifact_schema_validation():
    result = _valid_runtime_result()
    result["artifactProposals"][0]["reviewMarkers"] = []

    ok, blockers = validate_runtime_result(result)

    assert not ok
    assert "MISSING_REVIEW_MARKERS" in blockers
    assert any("RUNNER_RESULT_SCHEMA_INVALID" in blocker and "reviewMarkers" in blocker for blocker in blockers)
    assert any("ARTIFACT_SCHEMA_INVALID" in blocker and "reviewMarkers" in blocker for blocker in blockers)
