from __future__ import annotations

import json
import re
from typing import Any

from .java_mybatis_validator import JAVA_MYBATIS_SUFFIX_BY_ARTIFACT_TYPE, validate_java_mybatis_artifact
from .redaction_validator import find_redaction_violations
from .schema_validator import validate_artifact_proposal_schema, validate_runner_result_schema
from .sql_preview_validator import validate_table_design_preview

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

FORBIDDEN_OUTPUT_PATTERNS = [
    re.compile(r"\bexec(?:ute)?\s+(?:\[?[A-Za-z_][\w$#@]*\]?\.){0,2}\[?[A-Za-z_][\w$#@]*\]?", re.I),
    re.compile(r"\bcall\s+(?:\[?[A-Za-z_][\w$#@]*\]?\.){0,2}\[?[A-Za-z_][\w$#@]*\]?", re.I),
    re.compile("(?:\ud504\ub85c\uc2dc\uc800|procedure).{0,40}(?:\uc2e4\ud589|\ud638\ucd9c)", re.I),
]


def validate_runtime_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    blockers.extend(validate_runner_result_schema(result))

    if result.get("productionReady") is not False:
        blockers.append("PRODUCTION_READY_TRUE_BLOCKED")

    text = json.dumps(result, ensure_ascii=False)
    blockers.extend(find_redaction_violations(text))

    lowered = text.lower()
    for phrase in FORBIDDEN_OUTPUT_PHRASES:
        if phrase in lowered:
            blockers.append("EXECUTABLE_APPLY_INSTRUCTION")
    if any(pattern.search(text) for pattern in FORBIDDEN_OUTPUT_PATTERNS):
        blockers.append("EXECUTABLE_APPLY_INSTRUCTION")

    for artifact in result.get("artifactProposals", []):
        blockers.extend(validate_artifact_proposal_schema(artifact))
        artifact_type = artifact.get("artifactType")
        if artifact_type in RETIRED_ARTIFACT_TYPES:
            blockers.append(f"RETIRED_ARTIFACT_TYPE:{artifact_type}")
        if artifact_type and artifact_type not in ALLOWED_ARTIFACT_TYPES:
            # Table design preview is allowed as preview, but not as a persisted artifact.
            if artifact_type != "TABLE_DESIGN_PREVIEW":
                blockers.append(f"UNKNOWN_ARTIFACT_TYPE:{artifact_type}")
        if not artifact.get("evidenceRefs"):
            blockers.append("MISSING_EVIDENCE_REFS")
        if not artifact.get("reviewMarkers"):
            blockers.append("MISSING_REVIEW_MARKERS")
        if artifact_type and "REVIEW_REQUIRED" not in str(artifact.get("contentMarkdown") or ""):
            blockers.append("MISSING_REVIEW_MARKER_IN_CONTENT")
        if artifact_type == "TABLE_DESIGN_PREVIEW":
            ok, static_blockers = validate_table_design_preview(
                str(artifact.get("createTableScriptPreview") or ""),
                blocked_from_auto_apply=artifact.get("blockedFromAutoApply") is True,
            )
            if not ok:
                blockers.extend(f"TABLE_DESIGN_PREVIEW_STATIC:{blocker}" for blocker in static_blockers)
        if artifact_type in JAVA_MYBATIS_SUFFIX_BY_ARTIFACT_TYPE:
            ok, static_blockers = validate_java_mybatis_artifact(str(artifact_type), artifact)
            if not ok:
                blockers.extend(f"JAVA_MYBATIS_STATIC:{blocker}" for blocker in static_blockers)

    return (not blockers, blockers)
