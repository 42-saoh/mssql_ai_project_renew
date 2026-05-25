from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, TypedDict


@dataclass
class OrchestratorState:
    conversation_id: str
    chat_run_id: str
    actor_id: str
    sanitized_message_summary: str
    intent: str | None = None
    policy_decision: str | None = None
    target_key: str | None = None
    evidence_bundle_ref: str | None = None
    codex_run_id: str | None = None
    artifact_ids: list[str] = field(default_factory=list)
    review_markers: list[str] = field(default_factory=list)
    blocked_reason: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class OrchestratorGraphState(TypedDict, total=False):
    schemaVersion: str
    conversationId: str
    chatRunId: str
    sanitizedMessageSummary: str
    intent: str
    policyDecision: str
    blockers: list[str]
    route: str
    targetKey: str
    evidenceBundleRef: str | None
    runnerRequest: dict[str, Any]
    artifactIds: list[str]
    reviewMarkers: list[str]
    pgptUsed: bool
    pgptModel: str | None
    pgptFallbackReason: str | None
    pgptReasonSummary: str | None
    steps: list[str]


def initial_orchestrator_state(
    *,
    conversation_id: str | None = None,
    chat_run_id: str | None = None,
) -> OrchestratorGraphState:
    state: OrchestratorGraphState = {
        "schemaVersion": "OrchestratorState.v1",
        "sanitizedMessageSummary": "Sanitized DB analysis request.",
        "blockers": [],
        "artifactIds": [],
        "reviewMarkers": [],
        "pgptUsed": False,
        "steps": [],
    }
    if conversation_id:
        state["conversationId"] = conversation_id
    if chat_run_id:
        state["chatRunId"] = chat_run_id
    return state


def append_step(state: Mapping[str, Any], step: str) -> list[str]:
    return [*list(state.get("steps", [])), step]


def safe_checkpoint_from_state(state: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint: dict[str, Any] = {
        "schemaVersion": "OrchestratorCheckpoint.v1",
        "conversationId": state.get("conversationId"),
        "chatRunId": state.get("chatRunId"),
        "sanitizedMessageSummary": state.get("sanitizedMessageSummary"),
        "intent": state.get("intent"),
        "policyDecision": state.get("policyDecision"),
        "blockers": list(state.get("blockers", [])),
        "route": state.get("route"),
        "targetKey": state.get("targetKey"),
        "evidenceBundleRef": state.get("evidenceBundleRef"),
        "artifactIds": list(state.get("artifactIds", [])),
        "reviewMarkers": list(state.get("reviewMarkers", [])),
        "pgptUsed": bool(state.get("pgptUsed", False)),
        "pgptModel": state.get("pgptModel"),
        "pgptFallbackReason": state.get("pgptFallbackReason"),
        "pgptReasonSummary": state.get("pgptReasonSummary"),
        "steps": list(state.get("steps", [])),
    }
    runner_request = state.get("runnerRequest")
    if isinstance(runner_request, dict):
        checkpoint["runnerRequest"] = {
            "runType": runner_request.get("runType"),
            "target": {
                "targetKey": (runner_request.get("target") or {}).get("targetKey", "unresolved"),
            },
            "mode": runner_request.get("mode", "fake"),
        }
    return checkpoint
