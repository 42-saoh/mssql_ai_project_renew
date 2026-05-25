from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from apps.api.api_app.repositories import observability_repository
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist
from plf_agent_validation.redaction_validator import find_redaction_violations

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SAFE_BLOCKER_CODE = re.compile(r"^[A-Za-z0-9_:$.\[\]-]+$")
_REDACTION_BLOCKER_CODES = {
    "CONNECTION_STRING",
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "RAW_SP",
    "ROW_DATA",
    "SECRET",
}
_ALLOWED_CONTEXT_FIELDS = {
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
}


class ObservabilityEventError(ValueError):
    pass


def record_observability_event(
    event_type: str,
    *,
    subject_type: str,
    subject_id: str,
    created_at: str | None = None,
    **context: Any,
) -> dict[str, object]:
    event = build_observability_event(
        event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        created_at=created_at,
        **context,
    )
    return observability_repository.put(str(event["event_id"]), event)


def build_observability_event(
    event_type: str,
    *,
    subject_type: str,
    subject_id: str,
    created_at: str | None = None,
    **context: Any,
) -> dict[str, object]:
    _assert_safe_name(event_type, label="event_type")
    _assert_safe_name(subject_type, label="subject_type")
    _assert_safe_name(subject_id, label="subject_id")
    unknown_fields = sorted(set(context) - _ALLOWED_CONTEXT_FIELDS)
    if unknown_fields:
        raise ObservabilityEventError(f"Unsupported observability fields: {', '.join(unknown_fields)}")

    event: dict[str, object] = {
        "event_id": f"obs_{uuid4().hex[:12]}",
        "event_type": event_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "created_at": created_at or datetime.now(UTC).isoformat(),
    }
    for key, value in context.items():
        if value is None:
            continue
        if key == "blocker_codes":
            event[key] = _safe_blocker_codes(value if isinstance(value, Iterable) and not isinstance(value, str) else [value])
        else:
            event[key] = _safe_scalar(value, label=key)

    assert_safe_to_persist(event)
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
    raise ObservabilityEventError(f"Unsupported observability value for {label}.")


def _assert_safe_name(value: str, *, label: str) -> None:
    if not _SAFE_NAME.fullmatch(value):
        raise ObservabilityEventError(f"Unsafe {label}.")
