from __future__ import annotations

from copy import deepcopy
import re
from collections.abc import Iterable
from typing import Any

from plf_agent_validation.redaction_validator import find_redaction_violations

_STORE: dict[str, dict] = {}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SAFE_BLOCKER_CODE = re.compile(r"^[A-Za-z0-9_:$.\[\]-]+$")
_ALLOWED_EVENT_FIELDS = {
    "event_id",
    "event_type",
    "subject_type",
    "subject_id",
    "actor_id",
    "approval_id",
    "approval_type",
    "artifact_id",
    "artifact_type",
    "blocker_codes",
    "chat_run_id",
    "codex_run_id",
    "conversation_id",
    "intent",
    "policy_decision",
    "route",
    "run_type",
    "runner_mode",
    "status",
    "target_key",
    "validation_id",
    "validation_status",
    "created_at",
}
_REQUIRED_EVENT_FIELDS = {"event_id", "event_type", "subject_type", "subject_id", "created_at"}
_SAFE_NAME_FIELDS = {"event_id", "event_type", "subject_type", "subject_id"}
_REDACTION_BLOCKER_CODES = {
    "CONNECTION_STRING",
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "RAW_SP",
    "ROW_DATA",
    "SECRET",
}


class ObservabilityRepositoryError(ValueError):
    pass


def put(key: str, value: dict) -> dict:
    safe_event = _sanitize_event(value)
    if key != safe_event["event_id"]:
        raise ObservabilityRepositoryError("Observability key must match event_id.")
    _STORE[key] = deepcopy(safe_event)
    return deepcopy(_STORE[key])


def get(key: str) -> dict | None:
    value = _STORE.get(key)
    return deepcopy(value) if value is not None else None


def list_all() -> list[dict]:
    return [deepcopy(value) for value in _STORE.values()]


def clear() -> None:
    _STORE.clear()


def _sanitize_event(value: dict[str, Any]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ObservabilityRepositoryError("Observability event must be an object.")
    unknown_fields = sorted(set(value) - _ALLOWED_EVENT_FIELDS)
    if unknown_fields:
        raise ObservabilityRepositoryError(f"Unsupported observability fields: {', '.join(unknown_fields)}")
    missing_fields = sorted(_REQUIRED_EVENT_FIELDS - set(value))
    if missing_fields:
        raise ObservabilityRepositoryError(f"Missing observability fields: {', '.join(missing_fields)}")

    event: dict[str, object] = {}
    for field, raw_value in value.items():
        if raw_value is None:
            continue
        if field == "blocker_codes":
            blockers = raw_value if isinstance(raw_value, Iterable) and not isinstance(raw_value, str) else [raw_value]
            event[field] = _safe_blocker_codes(blockers)
            continue
        safe_value = _safe_scalar(raw_value, label=field)
        if field in _SAFE_NAME_FIELDS and not _SAFE_NAME.fullmatch(str(safe_value)):
            raise ObservabilityRepositoryError(f"Unsafe observability value for {field}.")
        if isinstance(safe_value, str) and find_redaction_violations(safe_value):
            raise ObservabilityRepositoryError(f"Unsafe observability value for {field}.")
        event[field] = safe_value
    return event


def _safe_blocker_codes(blockers: Iterable[object]) -> list[str]:
    safe: list[str] = []
    for blocker in blockers:
        code = str(blocker)
        if code in _REDACTION_BLOCKER_CODES or find_redaction_violations(code):
            safe_code = "REDACTION_VIOLATION_BLOCKED"
        elif _SAFE_BLOCKER_CODE.fullmatch(code):
            safe_code = code
        else:
            safe_code = "UNSAFE_BLOCKER_CODE"
        if safe_code not in safe:
            safe.append(safe_code)
    return safe


def _safe_scalar(value: object, *, label: str) -> str | bool | int | float:
    if isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value
    raise ObservabilityRepositoryError(f"Unsupported observability value for {label}.")
