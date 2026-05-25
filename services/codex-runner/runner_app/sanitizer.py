from __future__ import annotations

import json
import re
from typing import Any

from plf_agent_validation.redaction_validator import find_redaction_violations

ALLOWED_RUN_TYPES = {"SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"}
_BLOCKER_CODE = re.compile(r"[^A-Z0-9_]+")
_REDACTION_CODES = {
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "ROW_DATA",
    "CONNECTION_STRING",
    "SECRET",
    "RAW_SP",
}
_ALLOWED_BLOCKER_PREFIXES = {
    "ARTIFACT_PROPOSALS_NOT_ALLOWED_FOR_STATUS",
    "ARTIFACT_SCHEMA_INVALID",
    "CODEX_EXEC_ERROR",
    "CODEX_EXEC_FAILED",
    "CODEX_EXEC_TIMEOUT",
    "EXECUTABLE_APPLY_INSTRUCTION",
    "FINAL_OUTPUT_JSON_INVALID",
    "JAVA_MYBATIS_STATIC",
    "MISSING_EVIDENCE_REFS",
    "MISSING_FINAL_OUTPUT",
    "MISSING_REVIEW_MARKER_IN_CONTENT",
    "MISSING_REVIEW_MARKERS",
    "NON_RUNTIME_SKILL_BLOCKED",
    "OUTPUT_SCHEMA_BLOCKED",
    "PRODUCTION_READY_TRUE_BLOCKED",
    "RETIRED_ARTIFACT_TYPE",
    "RUNNER_BLOCKED",
    "RUNNER_OUTPUT_BLOCKED",
    "RUNNER_OUTPUT_FAILED",
    "RUNNER_POLICY_ALLOWS_BLOCKED_OPERATION",
    "RUNNER_RESULT_SCHEMA_INVALID",
    "RUNTIME_OUTPUT_SCHEMA_INVALID",
    "TABLE_DESIGN_PREVIEW_STATIC",
    "UNKNOWN_ARTIFACT_TYPE",
    "WORKSPACE_CONTRACT_BLOCKED",
    *_REDACTION_CODES,
}
_NO_DETAIL_PREFIXES = {
    "NON_RUNTIME_SKILL_BLOCKED",
    "RETIRED_ARTIFACT_TYPE",
    "UNKNOWN_ARTIFACT_TYPE",
}


def sanitize_result(result: dict[str, Any], request: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    text = json.dumps(result, ensure_ascii=False, default=str)
    violations = find_redaction_violations(text)
    if violations:
        return safe_blocked_result(request, violations), violations
    sanitized = dict(result)
    sanitized["blockers"] = safe_blocker_codes(list(sanitized.get("blockers") or []))
    return sanitized, violations


def safe_blocked_result(
    request: dict[str, Any] | None,
    blockers: list[str],
    *,
    validation: dict[str, bool] | None = None,
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = request or {}
    run_type = request.get("runType")
    if run_type not in ALLOWED_RUN_TYPES:
        run_type = "SP_ANALYSIS"
    target = request.get("target") if isinstance(request.get("target"), dict) else {}
    target_key = str(request.get("targetKey") or target.get("targetKey") or "unresolved")
    result: dict[str, Any] = {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": run_type,
        "targetKey": target_key,
        "status": "BLOCKED",
        "productionReady": False,
        "reviewRequired": True,
        "artifactProposals": [],
        "blockers": safe_blocker_codes(blockers or ["RUNNER_BLOCKED"]),
        "validation": {
            "schemaValid": False,
            "policyValid": False,
            "staticValidationPassed": False,
        },
    }
    if validation:
        result["validation"].update(validation)
    if runtime:
        result["runtime"] = runtime
    return result


def safe_blocker_codes(blockers: list[str]) -> list[str]:
    return _dedupe([_safe_blocker_code(blocker) for blocker in blockers] or ["RUNNER_BLOCKED"])


def _safe_blocker_code(blocker: Any) -> str:
    raw = str(blocker or "")
    parts = raw.split(":")
    prefix = _normalize_code_part(parts[0])
    if not prefix:
        return "RUNNER_BLOCKED"
    if prefix not in _ALLOWED_BLOCKER_PREFIXES:
        return "RUNNER_BLOCKED"
    if prefix in _REDACTION_CODES and len(parts) == 1:
        return prefix
    if prefix in _NO_DETAIL_PREFIXES:
        return prefix

    safe_parts: list[str] = []
    for detail in parts[1:]:
        safe_detail = _normalize_code_part(detail)
        if find_redaction_violations(str(detail)) and str(detail) != safe_detail:
            safe_parts.append("UNSAFE_VALUE")
            continue
        if safe_detail:
            safe_parts.append(safe_detail)
    if not safe_parts:
        return prefix
    return ":".join([prefix, *safe_parts])


def _normalize_code_part(value: Any) -> str:
    normalized = _BLOCKER_CODE.sub("_", str(value or "").upper()).strip("_")
    return re.sub(r"_+", "_", normalized)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
