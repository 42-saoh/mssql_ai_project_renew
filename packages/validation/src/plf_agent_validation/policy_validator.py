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

_SQL_ACTION = r"(?:apply|run|execute|submit|issue)"
_SOURCE_ACTION = r"(?:apply|overwrite|replace|write|patch)"
_DEPLOY_ACTION = r"(?:deploy|release|roll\s*out)"
_OPTIONAL_OUTPUT_REF = r"(?:(?:this|the\s+following|the|following|generated|provided)\s+)?"
_SQL_OBJECT_ACTION = r"(?:create|alter|drop)\s+(?:table|view|index|proc(?:edure)?|function|trigger)"
_DML_ACTION = r"(?:insert|update|delete|merge)"
_SQL_TARGET = (
    r"(?:ddl|dml|sql|query|statement|script|migration|schema\s+change|database\s+change)"
)
_SOURCE_TARGET = r"(?:source|source\s+code|code|files?|java\s+files?|mapper\s+files?)"
_DEPLOY_TARGET = r"(?:service|application|app|artifact|build|code|changes?)"
_SQL_IDENTIFIER = r"(?:\[?[A-Za-z_][\w$#@]*\]?)"
_DOTTED_SQL_OBJECT = rf"{_SQL_IDENTIFIER}(?:\s*\.\s*{_SQL_IDENTIFIER}){{0,2}}"

FORBIDDEN_OUTPUT_PATTERNS = [
    re.compile(rf"\b{_SQL_ACTION}\s+{_OPTIONAL_OUTPUT_REF}{_SQL_TARGET}\b", re.I),
    re.compile(rf"\b{_SQL_ACTION}\s+{_OPTIONAL_OUTPUT_REF}{_SQL_OBJECT_ACTION}\b", re.I),
    re.compile(rf"\b{_SQL_ACTION}\s+{_OPTIONAL_OUTPUT_REF}{_DML_ACTION}\b", re.I),
    re.compile(rf"\b{_SQL_TARGET}\s+(?:should\s+be\s+|must\s+be\s+|can\s+be\s+)?(?:applied|run|executed)\b", re.I),
    re.compile(r"\b(?:run|call|exec(?:ute)?)\s+(?:(?:this|the|following)\s+)?(?:stored\s+)?(?:proc(?:edure)?|sp)\b", re.I),
    re.compile(r"\b(?:stored\s+)?(?:proc(?:edure)?|sp)\s+(?:should\s+be\s+|must\s+be\s+|can\s+be\s+)?(?:run|called|executed)\b", re.I),
    re.compile(rf"\bexec(?:ute)?\s+{_DOTTED_SQL_OBJECT}", re.I),
    re.compile(rf"\bcall\s+{_DOTTED_SQL_OBJECT}", re.I),
    re.compile(rf"\b{_SOURCE_ACTION}\s+{_OPTIONAL_OUTPUT_REF}{_SOURCE_TARGET}\b", re.I),
    re.compile(rf"\b{_SOURCE_TARGET}\s+(?:should\s+be\s+|must\s+be\s+|can\s+be\s+)?(?:applied|overwritten|replaced|patched|written)\b", re.I),
    re.compile(rf"\b{_DEPLOY_ACTION}\s+{_OPTIONAL_OUTPUT_REF}{_DEPLOY_TARGET}\b", re.I),
    re.compile(r"\bdeploy\s+automatically\b", re.I),
    re.compile(rf"\b{_DEPLOY_TARGET}\s+(?:should\s+be\s+|must\s+be\s+|can\s+be\s+)?(?:deployed|released|rolled\s*out)\b", re.I),
    re.compile(r"(?:ddl|dml|sql|\ucffc\ub9ac|\ub9c8\uc774\uadf8\ub808\uc774\uc158).{0,30}(?:\uc801\uc6a9|\uc2e4\ud589|\uc218\ud589|\ub3cc\ub824)", re.I),
    re.compile(r"(?:\uc18c\uc2a4|\ucf54\ub4dc).{0,30}(?:\uc801\uc6a9|\ub36e\uc5b4\uc4f0|\ubc18\uc601|\ubc30\ud3ec)", re.I),
    re.compile(r"\ubc30\ud3ec.{0,30}(?:\uc2e4\ud589|\uc218\ud589|\ud558)", re.I),
    re.compile("(?:\uc800\uc7a5\\s*)?\ud504\ub85c\uc2dc\uc800(?:\\s*(?:\uc744|\ub97c))?\\s*(?:\uc2e4\ud589|\ud638\ucd9c)", re.I),
    re.compile("(?:\ud504\ub85c\uc2dc\uc800|procedure).{0,40}(?:\uc2e4\ud589|\ud638\ucd9c)", re.I),
]


def validate_runtime_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    blockers.extend(validate_runner_result_schema(result))

    if result.get("productionReady") is not False:
        blockers.append("PRODUCTION_READY_TRUE_BLOCKED")

    text = json.dumps(result, ensure_ascii=False)
    blockers.extend(find_redaction_violations(text))

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

    blockers = _dedupe(blockers)
    return (not blockers, blockers)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
