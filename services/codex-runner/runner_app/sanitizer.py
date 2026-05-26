from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from typing import Any

from plf_agent_validation.redaction_validator import find_redaction_violations

ALLOWED_RUN_TYPES = {"SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"}
_BLOCKER_CODE = re.compile(r"[^A-Z0-9_]+")
_SAFE_TARGET_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
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


def sanitize_result(result: Any, request: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    text = json.dumps(result, ensure_ascii=False, default=str)
    violations = find_redaction_violations(text)
    shape_blockers = _result_shape_blockers(result)
    if violations or shape_blockers:
        blockers = [*shape_blockers, *violations]
        return safe_blocked_result(request, blockers), blockers
    sanitized = dict(result)
    sanitized["blockers"] = safe_blocker_codes(sanitized.get("blockers"))
    return sanitized, violations


def _result_shape_blockers(result: Any) -> list[str]:
    if not isinstance(result, Mapping):
        return ["RUNNER_RESULT_SCHEMA_INVALID"]
    blockers: list[str] = []
    if "artifactProposals" in result:
        proposals = result.get("artifactProposals")
        if not isinstance(proposals, list) or any(not isinstance(item, Mapping) for item in proposals):
            blockers.append("RUNNER_RESULT_SCHEMA_INVALID")
    if "validation" in result and not isinstance(result.get("validation"), Mapping):
        blockers.append("RUNNER_RESULT_SCHEMA_INVALID")
    return _dedupe(blockers)


def safe_blocked_result(
    request: dict[str, Any] | None,
    blockers: Any,
    *,
    validation: dict[str, bool] | None = None,
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = request if isinstance(request, Mapping) else {}
    run_type = request.get("runType")
    if run_type not in ALLOWED_RUN_TYPES:
        run_type = "SP_ANALYSIS"
    target_key = _safe_target_key(request)
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


def _safe_target_key(request: Mapping[str, Any]) -> str:
    target = request.get("target") if isinstance(request.get("target"), dict) else {}
    for candidate in (request.get("targetKey"), target.get("targetKey")):
        value = str(candidate or "").strip()
        if _is_safe_target_key(value):
            return value
    return "unresolved"


def _is_safe_target_key(value: str) -> bool:
    return bool(value and _SAFE_TARGET_KEY.fullmatch(value) and not find_redaction_violations(value))


def safe_blocker_codes(blockers: Any) -> list[str]:
    return _dedupe([_safe_blocker_code(blocker) for blocker in _blocker_values(blockers)] or ["RUNNER_BLOCKED"])


def _blocker_values(blockers: Any) -> list[Any]:
    if blockers is None:
        return []
    if isinstance(blockers, str):
        return [blockers]
    if isinstance(blockers, Mapping):
        return list(blockers.keys()) or ["RUNNER_BLOCKED"]
    if isinstance(blockers, Iterable):
        return list(blockers)
    return [blockers]


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
