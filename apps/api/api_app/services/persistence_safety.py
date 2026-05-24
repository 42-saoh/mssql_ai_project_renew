from __future__ import annotations

import json
from typing import Any

from plf_agent_validation.redaction_validator import find_redaction_violations


class PersistenceSafetyError(ValueError):
    def __init__(self, violations: list[str]):
        super().__init__("Payload contains content blocked from persistence.")
        self.violations = violations


def assert_safe_to_persist(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    violations = find_redaction_violations(text)
    if violations:
        raise PersistenceSafetyError(violations)


def summarize_user_message(message: str, *, intent: str, route: str) -> str:
    if route == "blocked":
        return "Blocked request summary."
    if intent == "METADATA_SEARCH":
        return "Metadata search request summary."
    if intent == "HISTORY_LOOKUP":
        return "History lookup request summary."
    if intent in {"SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"}:
        return f"{intent} request summary."
    return "DB analysis request summary."


def content_ref_for_artifact(artifact_id: str) -> str:
    return f"memory://artifacts/{artifact_id}/content"
