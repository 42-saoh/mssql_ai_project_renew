from __future__ import annotations

from plf_agent_contracts.enums import Intent

from .intents import classify_intent
from .langsmith_config import LangSmithTraceContextFactory
from .pgpt_client import PgptClassification, PgptClientError, PgptResponsesClient, sanitize_reason_summary
from .policy_gate import policy_decision

_PGPT_ASSISTED_INTENTS = {
    Intent.SP_ANALYSIS,
    Intent.METADATA_SEARCH,
    Intent.DEPENDENCY_ANALYSIS,
    Intent.TABLE_DESIGN,
    Intent.DRAFT_GENERATION,
}


def orchestrate_message(
    message: str,
    pgpt_client: PgptResponsesClient | None = None,
    langsmith_trace: LangSmithTraceContextFactory | None = None,
) -> dict[str, object]:
    """Small deterministic MVP before LangGraph wiring.

    The PGPT Responses API may assist allowed DB-analysis intent routing, but
    deterministic policy gates remain the safety fallback.
    """
    trace = langsmith_trace or LangSmithTraceContextFactory.from_env()
    with trace.context(metadata=trace.settings.safe_metadata(_trace_preview(message))):
        return _orchestrate_message(message, pgpt_client=pgpt_client)


def _orchestrate_message(
    message: str,
    pgpt_client: PgptResponsesClient | None = None,
) -> dict[str, object]:
    intent = classify_intent(message)
    decision, blockers = policy_decision(message, intent)
    pgpt = pgpt_client or PgptResponsesClient.from_env()

    pgpt_used = False
    pgpt_fallback_reason: str | None = None
    pgpt_reason_summary: str | None = None

    if decision != "ALLOW":
        pgpt_fallback_reason = "POLICY_BLOCKED_BEFORE_PGPT"
    elif intent not in _PGPT_ASSISTED_INTENTS:
        pgpt_fallback_reason = "INTENT_NOT_PGPT_ASSISTED"
    else:
        try:
            classification = pgpt.classify_message(message)
            intent, decision, blockers, pgpt_used, pgpt_reason_summary = _apply_pgpt_classification(
                message,
                classification,
            )
        except PgptClientError as exc:
            pgpt_fallback_reason = exc.code

    return {
        "intent": intent.value,
        "policyDecision": decision,
        "blockers": blockers,
        "route": _route_for(intent.value, decision),
        "pgptUsed": pgpt_used,
        "pgptModel": pgpt.settings.model,
        "pgptFallbackReason": pgpt_fallback_reason,
        "pgptReasonSummary": pgpt_reason_summary,
    }


def _apply_pgpt_classification(
    message: str,
    classification: PgptClassification,
) -> tuple[Intent, str, list[str], bool, str | None]:
    if classification.intent is None:
        raise PgptClientError("PGPT_MISSING_INTENT", "PGPT did not return an intent.")
    decision, blockers = policy_decision(message, classification.intent)
    return (
        classification.intent,
        decision,
        blockers,
        True,
        sanitize_reason_summary(classification.reason_summary, original_message=message),
    )


def _trace_preview(message: str) -> dict[str, object]:
    intent = classify_intent(message)
    decision, _blockers = policy_decision(message, intent)
    return {
        "intent": intent.value,
        "policyDecision": decision,
        "route": _route_for(intent.value, decision),
        "pgptUsed": False,
    }


def _route_for(intent: str, decision: str) -> str:
    if decision != "ALLOW":
        return "blocked"
    if intent == "METADATA_SEARCH":
        return "metadata_gateway"
    if intent == "HISTORY_LOOKUP":
        return "history_store"
    if intent in {"SP_ANALYSIS", "DEPENDENCY_ANALYSIS", "TABLE_DESIGN", "DRAFT_GENERATION"}:
        return "codex_runner"
    return "blocked"
