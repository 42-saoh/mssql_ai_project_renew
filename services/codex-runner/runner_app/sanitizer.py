from __future__ import annotations

from plf_agent_validation.redaction_validator import find_redaction_violations


def sanitize_result(result: dict) -> tuple[dict, list[str]]:
    text = str(result)
    violations = find_redaction_violations(text)
    return result, violations
