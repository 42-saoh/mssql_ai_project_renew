from __future__ import annotations


def run_fake(request: dict, evidence_bundle: dict | None = None) -> dict:
    run_type = request.get("runType", "SP_ANALYSIS")
    target = request.get("target", {})
    target_key = target.get("targetKey", "unknown")
    artifact_type = {
        "SP_ANALYSIS": "SP_ANALYSIS_DOC",
        "DEPENDENCY_ANALYSIS": "DEPENDENCY_REPORT",
        "DRAFT_GENERATION": "DTO_DRAFT",
    }.get(run_type, "TABLE_DESIGN_PREVIEW")
    artifact = {
        "artifactType": artifact_type,
        "title": f"{run_type} proposal",
        "contentMarkdown": "Generated scaffold proposal. REVIEW_REQUIRED.",
        "evidenceRefs": ["evidence.scaffold"],
        "reviewMarkers": ["REVIEW_REQUIRED"],
    }
    if artifact_type == "TABLE_DESIGN_PREVIEW":
        artifact.update(
            {
                "previewType": "TABLE_DESIGN_PREVIEW",
                "createTableScriptPreview": "CREATE TABLE dbo.ReviewRequiredPreview (id int NOT NULL);",
                "reviewRequired": True,
                "blockedFromAutoApply": True,
            }
        )
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": run_type,
        "targetKey": target_key,
        "status": "SUCCEEDED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [artifact],
        "blockers": [],
        "validation": {"schemaValid": True, "policyValid": True, "staticValidationPassed": True},
    }
