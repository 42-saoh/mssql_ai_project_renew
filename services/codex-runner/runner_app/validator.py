from __future__ import annotations

from plf_agent_validation.policy_validator import validate_runtime_result


def validate_result(result: dict) -> tuple[bool, list[str]]:
    return validate_runtime_result(result)
