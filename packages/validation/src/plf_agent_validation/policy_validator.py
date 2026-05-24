from __future__ import annotations

import json
from typing import Any

from .redaction_validator import find_redaction_violations

ALLOWED_ARTIFACT_TYPES = {
    "SP_ANALYSIS_DOC",
    "DEPENDENCY_REPORT",
    "DTO_DRAFT",
    "SERVICE_DRAFT",
    "MAPPER_INTERFACE",
    "MAPPER_XML",
}

RETIRED_ARTIFACT_TYPES = {"DDL_DRAFT", "VO_DRAFT", "MODEL_DRAFT"}

FORBIDDEN_OUTPUT_PHRASES = [
    "apply this ddl",
    "execute this sql",
    "run this procedure",
    "deploy automatically",
]


def validate_runtime_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []

    if result.get("productionReady") is not False:
        blockers.append("PRODUCTION_READY_TRUE_BLOCKED")

    text = json.dumps(result, ensure_ascii=False)
    blockers.extend(find_redaction_violations(text))

    lowered = text.lower()
    for phrase in FORBIDDEN_OUTPUT_PHRASES:
        if phrase in lowered:
            blockers.append("EXECUTABLE_APPLY_INSTRUCTION")

    for artifact in result.get("artifactProposals", []):
        artifact_type = artifact.get("artifactType")
        if artifact_type in RETIRED_ARTIFACT_TYPES:
            blockers.append(f"RETIRED_ARTIFACT_TYPE:{artifact_type}")
        if artifact_type and artifact_type not in ALLOWED_ARTIFACT_TYPES:
            # Table design preview is allowed as preview, but not as a persisted artifact.
            if artifact_type != "TABLE_DESIGN_PREVIEW":
                blockers.append(f"UNKNOWN_ARTIFACT_TYPE:{artifact_type}")
        if not artifact.get("reviewMarkers"):
            blockers.append("MISSING_REVIEW_MARKERS")

    return (not blockers, blockers)
