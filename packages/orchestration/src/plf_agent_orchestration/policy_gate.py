from __future__ import annotations

from plf_agent_contracts.enums import Intent

from .forbidden_operations import detect_forbidden_operation_blockers, has_hard_blocker

FORBIDDEN_TERMS = [
    "row data",
    "select *",
    "프로시저 실행",
    "sp 실행",
    "ddl 적용",
    "dml 적용",
    "deploy",
    "배포",
]


def policy_decision(message: str, intent: Intent) -> tuple[str, list[str]]:
    text = (message or "").lower()
    blockers = detect_forbidden_operation_blockers(message)
    blockers.extend(term for term in FORBIDDEN_TERMS if term in text and term not in blockers)
    if intent == Intent.BLOCKED:
        blockers.append("OUT_OF_DOMAIN")
    if intent == Intent.BLOCKED_OR_APPROVAL_REQUIRED and not blockers:
        blockers.append("MANUAL_REVIEW_REQUIRED")
    if blockers:
        if "OUT_OF_DOMAIN" in blockers or has_hard_blocker(blockers):
            return "BLOCKED", blockers
        return "BLOCKED_OR_APPROVAL_REQUIRED", blockers
    return "ALLOW", []
