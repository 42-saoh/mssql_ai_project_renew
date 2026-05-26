from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from plf_agent_validation.policy_validator import validate_runtime_result
from plf_agent_validation.schema_validator import validate_runner_result_schema

DEFAULT_RUNTIME_SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "runtime-template" / "schemas"
PROPOSAL_ALLOWED_STATUSES = {"SUCCEEDED", "REVIEW_REQUIRED"}
FAILED_OR_BLOCKED_STATUSES = {"FAILED", "BLOCKED"}


def validate_result(
    result: Any,
    *,
    output_schema: str | Path | None = None,
    schema_root: str | Path | None = None,
) -> tuple[bool, list[str]]:
    _, blockers = validation_flags(result, output_schema=output_schema, schema_root=schema_root)
    return not blockers, blockers


def validation_flags(
    result: Any,
    *,
    output_schema: str | Path | None = None,
    schema_root: str | Path | None = None,
) -> tuple[dict[str, bool], list[str]]:
    schema_blockers = validate_runner_result_schema(result)
    schema_blockers.extend(_validate_runtime_output_schema(result, output_schema, schema_root))
    if not isinstance(result, Mapping):
        blockers = _dedupe(schema_blockers or ["RUNNER_RESULT_SCHEMA_INVALID"])
        return (
            {
                "schemaValid": False,
                "policyValid": False,
                "staticValidationPassed": False,
            },
            blockers,
        )
    ok, blockers = validate_runtime_result(result)
    status_blockers = _validate_status_artifact_consistency(result)
    status_blockers.extend(_validate_failed_or_blocked_status(result))
    if status_blockers:
        ok = False
        blockers.extend(status_blockers)
    blockers = _dedupe(schema_blockers + blockers)
    return (
        {
            "schemaValid": not schema_blockers,
            "policyValid": ok,
            "staticValidationPassed": not blockers,
        },
        blockers,
    )


def mark_validated(
    result: Any,
    *,
    output_schema: str | Path | None = None,
    schema_root: str | Path | None = None,
) -> tuple[dict, list[str]]:
    flags, blockers = validation_flags(result, output_schema=output_schema, schema_root=schema_root)
    validated = dict(result) if isinstance(result, Mapping) else {}
    existing_blockers = _as_list(validated.get("blockers"))
    validated["blockers"] = _dedupe(existing_blockers + blockers)
    validation_value = validated.get("validation")
    validation = dict(validation_value) if isinstance(validation_value, Mapping) else {}
    validation.update(flags)
    validated["validation"] = validation
    if blockers:
        validated["status"] = "BLOCKED"
    return validated, blockers


def _validate_status_artifact_consistency(result: dict[str, Any]) -> list[str]:
    if result.get("artifactProposals") and result.get("status") not in PROPOSAL_ALLOWED_STATUSES:
        return [f"ARTIFACT_PROPOSALS_NOT_ALLOWED_FOR_STATUS:{result.get('status') or 'UNKNOWN'}"]
    return []


def _validate_failed_or_blocked_status(result: dict[str, Any]) -> list[str]:
    status = str(result.get("status") or "")
    if status in FAILED_OR_BLOCKED_STATUSES:
        return [f"RUNNER_OUTPUT_{status}"]
    return []


def _validate_runtime_output_schema(
    result: Any,
    output_schema: str | Path | None,
    schema_root: str | Path | None,
) -> list[str]:
    if output_schema is None:
        return []

    try:
        schema_path = _resolve_runtime_schema_path(output_schema, schema_root)
    except ValueError as exc:
        return [f"RUNTIME_OUTPUT_SCHEMA_INVALID:$:{exc}"]
    if not schema_path.is_file():
        return [f"RUNTIME_OUTPUT_SCHEMA_INVALID:$:missing:{schema_path.name}"]

    validator = _runtime_validator(schema_path)
    return [
        f"RUNTIME_OUTPUT_SCHEMA_INVALID:{_json_path(error.absolute_path)}:{_validator_detail(error)}"
        for error in sorted(validator.iter_errors(result), key=lambda item: list(item.absolute_path))
    ]


def _resolve_runtime_schema_path(output_schema: str | Path, schema_root: str | Path | None) -> Path:
    schema_path = Path(str(output_schema))
    if schema_path.is_absolute():
        return schema_path
    if ".." in schema_path.parts:
        raise ValueError("parent traversal")
    if len(schema_path.parts) == 1:
        schema_path = Path("schemas") / schema_path
    if schema_path.parts[0] != "schemas" or schema_path.suffix != ".json":
        raise ValueError("schema must be a JSON file under schemas/")
    root = Path(schema_root) if schema_root is not None else DEFAULT_RUNTIME_SCHEMA_ROOT
    return root / Path(*schema_path.parts[1:])


@lru_cache(maxsize=None)
def _runtime_validator(schema_path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _validator_detail(error: Any) -> str:
    if error.validator == "const":
        return f"const:{error.validator_value}"
    if error.validator == "enum":
        return "enum"
    if error.validator == "required":
        return "required"
    return str(error.validator)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]
