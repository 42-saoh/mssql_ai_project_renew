from __future__ import annotations

from plf_agent_validation.policy_validator import validate_runtime_result
from plf_agent_validation.schema_validator import validate_runner_result_schema


def validate_result(result: dict) -> tuple[bool, list[str]]:
    return validate_runtime_result(result)


def validation_flags(result: dict) -> tuple[dict[str, bool], list[str]]:
    schema_blockers = validate_runner_result_schema(result)
    ok, blockers = validate_runtime_result(result)
    return (
        {
            "schemaValid": not schema_blockers,
            "policyValid": ok,
            "staticValidationPassed": ok,
        },
        blockers,
    )


def mark_validated(result: dict) -> tuple[dict, list[str]]:
    flags, blockers = validation_flags(result)
    validated = dict(result)
    existing_blockers = list(validated.get("blockers") or [])
    validated["blockers"] = _dedupe(existing_blockers + blockers)
    validation = dict(validated.get("validation") or {})
    validation.update(flags)
    validated["validation"] = validation
    if blockers:
        validated["status"] = "BLOCKED"
    return validated, blockers


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
