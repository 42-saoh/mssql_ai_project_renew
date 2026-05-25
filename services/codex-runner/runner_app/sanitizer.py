from __future__ import annotations

import json
from typing import Any

from plf_agent_validation.redaction_validator import find_redaction_violations

ALLOWED_RUN_TYPES = {"SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"}


def sanitize_result(result: dict[str, Any], request: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    text = json.dumps(result, ensure_ascii=False, default=str)
    violations = find_redaction_violations(text)
    if violations:
        return safe_blocked_result(request, violations), violations
    return result, violations


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
        "blockers": _dedupe(blockers or ["RUNNER_BLOCKED"]),
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


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
