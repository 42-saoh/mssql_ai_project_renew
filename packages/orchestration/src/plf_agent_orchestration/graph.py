from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from plf_agent_contracts.enums import Intent

from .intents import classify_intent
from .langsmith_config import LangSmithTraceContextFactory
from .pgpt_client import PgptClassification, PgptClientError, PgptResponsesClient, sanitize_reason_summary
from .policy_gate import policy_decision
from .state import (
    OrchestratorGraphState,
    append_step,
    initial_orchestrator_state,
    safe_checkpoint_from_state,
)

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
    *,
    conversation_id: str | None = None,
    chat_run_id: str | None = None,
) -> dict[str, object]:
    """Run the G05 LangGraph MVP without storing raw prompt text.

    The PGPT Responses API may assist allowed DB-analysis intent routing, but
    deterministic policy gates remain the safety fallback.
    """
    trace = langsmith_trace or LangSmithTraceContextFactory.from_env()
    with trace.context(metadata=trace.settings.safe_metadata(_trace_preview(message))):
        return _orchestrate_message(
            message,
            pgpt_client=pgpt_client,
            conversation_id=conversation_id,
            chat_run_id=chat_run_id,
        )


def _orchestrate_message(
    message: str,
    pgpt_client: PgptResponsesClient | None = None,
    *,
    conversation_id: str | None = None,
    chat_run_id: str | None = None,
) -> dict[str, object]:
    graph = build_chat_orchestrator_graph(message, pgpt_client=pgpt_client)
    thread_id = chat_run_id or conversation_id or "orchestrator-mvp"
    final_state = graph.invoke(
        initial_orchestrator_state(conversation_id=conversation_id, chat_run_id=chat_run_id),
        config={"configurable": {"thread_id": thread_id}},
    )
    checkpoint = safe_checkpoint_from_state(final_state)

    return {
        "intent": str(final_state.get("intent", Intent.BLOCKED.value)),
        "policyDecision": str(final_state.get("policyDecision", "BLOCKED")),
        "blockers": list(final_state.get("blockers", [])),
        "route": str(final_state.get("route", "blocked")),
        "pgptUsed": bool(final_state.get("pgptUsed", False)),
        "pgptModel": final_state.get("pgptModel"),
        "pgptFallbackReason": final_state.get("pgptFallbackReason"),
        "pgptReasonSummary": final_state.get("pgptReasonSummary"),
        "runnerRequest": final_state.get("runnerRequest"),
        "checkpoint": checkpoint,
        "orchestrator": {
            "engine": "langgraph",
            "checkpoint": "in_memory",
            "nodes": list(final_state.get("steps", [])),
        },
    }


def build_chat_orchestrator_graph(message: str, pgpt_client: PgptResponsesClient | None = None):
    builder = StateGraph(OrchestratorGraphState)
    builder.add_node("domain_guard", _domain_guard_node(message))
    builder.add_node("policy_gate", _policy_gate_node(message))
    builder.add_node("pgpt_intent_assist", _pgpt_intent_assist_node(message, pgpt_client))
    builder.add_node("route_intent", _route_intent_node)
    builder.add_node("prepare_fake_runner", _prepare_fake_runner_node)
    builder.add_edge(START, "domain_guard")
    builder.add_edge("domain_guard", "policy_gate")
    builder.add_edge("policy_gate", "pgpt_intent_assist")
    builder.add_edge("pgpt_intent_assist", "route_intent")
    builder.add_edge("route_intent", "prepare_fake_runner")
    builder.add_edge("prepare_fake_runner", END)
    return builder.compile(checkpointer=InMemorySaver())


def _domain_guard_node(message: str) -> Callable[[OrchestratorGraphState], dict[str, Any]]:
    def node(state: OrchestratorGraphState) -> dict[str, Any]:
        intent = classify_intent(message)
        return {
            "intent": intent.value,
            "steps": append_step(state, "domain_guard"),
        }

    return node


def _policy_gate_node(message: str) -> Callable[[OrchestratorGraphState], dict[str, Any]]:
    def node(state: OrchestratorGraphState) -> dict[str, Any]:
        intent = Intent(str(state.get("intent", Intent.BLOCKED.value)))
        decision, blockers = policy_decision(message, intent)
        return {
            "policyDecision": decision,
            "blockers": blockers,
            "steps": append_step(state, "policy_gate"),
        }

    return node


def _pgpt_intent_assist_node(
    message: str,
    pgpt_client: PgptResponsesClient | None,
) -> Callable[[OrchestratorGraphState], dict[str, Any]]:
    pgpt = pgpt_client or PgptResponsesClient.from_env()

    def node(state: OrchestratorGraphState) -> dict[str, Any]:
        intent = Intent(str(state.get("intent", Intent.BLOCKED.value)))
        decision = str(state.get("policyDecision", "BLOCKED"))
        updates: dict[str, Any] = {
            "pgptModel": pgpt.settings.model,
            "steps": append_step(state, "pgpt_intent_assist"),
        }
        if decision != "ALLOW":
            updates["pgptFallbackReason"] = "POLICY_BLOCKED_BEFORE_PGPT"
            return updates
        if intent not in _PGPT_ASSISTED_INTENTS:
            updates["pgptFallbackReason"] = "INTENT_NOT_PGPT_ASSISTED"
            return updates
        try:
            classification = pgpt.classify_message(message)
            intent, decision, blockers, pgpt_used, pgpt_reason_summary = _apply_pgpt_classification(
                message,
                classification,
            )
        except PgptClientError as exc:
            updates["pgptFallbackReason"] = exc.code
            return updates
        updates.update(
            {
                "intent": intent.value,
                "policyDecision": decision,
                "blockers": blockers,
                "pgptUsed": pgpt_used,
                "pgptFallbackReason": None,
                "pgptReasonSummary": pgpt_reason_summary,
            }
        )
        return updates

    return node


def _route_intent_node(state: OrchestratorGraphState) -> dict[str, Any]:
    decision = str(state.get("policyDecision", "BLOCKED"))
    intent = str(state.get("intent", Intent.BLOCKED.value))
    return {
        "route": _route_for(intent, decision),
        "steps": append_step(state, "route_intent"),
    }


def _prepare_fake_runner_node(state: OrchestratorGraphState) -> dict[str, Any]:
    route = str(state.get("route", "blocked"))
    decision = str(state.get("policyDecision", "BLOCKED"))
    updates: dict[str, Any] = {"steps": append_step(state, "prepare_fake_runner")}
    if route != "codex_runner" or decision != "ALLOW":
        return updates
    target_key = str(state.get("targetKey") or "unresolved")
    updates["runnerRequest"] = {
        "runType": str(state.get("intent")),
        "target": {"targetKey": target_key},
        "mode": "fake",
    }
    updates["targetKey"] = target_key
    return updates


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
