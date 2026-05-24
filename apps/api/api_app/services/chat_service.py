from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.auth import require_actor_id
from apps.api.api_app.repositories import approval_repository, conversation_repository, run_repository
from apps.api.api_app.services.codex_runner_client import submit_codex_run
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist, summarize_user_message
from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_validation.redaction_validator import find_redaction_violations


def create_chat_run(message: str, *, conversation_id: str | None = None, actor_id: str | None = None) -> dict[str, object]:
    actor = require_actor_id(actor_id)
    conversation_id = conversation_id or f"conv_{uuid4().hex[:12]}"
    chat_run_id = f"chatrun_{uuid4().hex[:12]}"
    routed = orchestrate_message(message)
    status = "ACCEPTED" if routed["policyDecision"] == "ALLOW" else "BLOCKED"
    now = _now()

    conversation = conversation_repository.get(conversation_id) or {
        "conversation_id": conversation_id,
        "actor_id": actor,
        "title": "DB analysis conversation",
        "created_at": now,
        "updated_at": now,
    }
    conversation["updated_at"] = now
    assert_safe_to_persist(conversation)
    conversation_repository.put(conversation_id, conversation)

    run_record = {
        "chat_run_id": chat_run_id,
        "conversation_id": conversation_id,
        "actor_id": actor,
        "user_message_summary": summarize_user_message(
            message,
            intent=str(routed["intent"]),
            route=str(routed["route"]),
        ),
        "intent": routed["intent"],
        "route": routed["route"],
        "status": status,
        "policy_decision": routed["policyDecision"],
        "blockers": _safe_blockers(list(routed.get("blockers", []))),
        "target_key": None,
        "pgpt_used": bool(routed.get("pgptUsed", False)),
        "pgpt_model": routed.get("pgptModel"),
        "pgpt_fallback_reason": routed.get("pgptFallbackReason"),
        "pgpt_reason_summary": routed.get("pgptReasonSummary"),
        "created_at": now,
        "completed_at": now if status == "BLOCKED" else None,
    }
    assert_safe_to_persist(run_record)
    run_repository.put_chat_run(chat_run_id, run_record)

    response: dict[str, object] = {
        "chatRunId": chat_run_id,
        "conversationId": conversation_id,
        "status": status,
        **routed,
    }

    if routed["route"] == "codex_runner" and routed["policyDecision"] == "ALLOW":
        codex_run = submit_codex_run(
            {
                "chatRunId": chat_run_id,
                "conversationId": conversation_id,
                "runType": routed["intent"],
                "targetKey": "unresolved",
            }
        )
        response["codexRunId"] = codex_run["codexRunId"]

    if routed["policyDecision"] == "BLOCKED_OR_APPROVAL_REQUIRED":
        approval_id = f"approval_{uuid4().hex[:12]}"
        approval = {
            "approval_id": approval_id,
            "chat_run_id": chat_run_id,
            "approval_type": "POLICY_REVIEW",
            "status": "PENDING",
            "reason": "Manual review required by policy gate.",
            "requested_at": now,
            "resolved_at": None,
        }
        assert_safe_to_persist(approval)
        approval_repository.put(approval_id, approval)
        response["approvalId"] = approval_id

    return response


def get_chat_run(chat_run_id: str) -> dict[str, object]:
    record = run_repository.get_chat_run(chat_run_id)
    if record is None:
        return {"chatRunId": chat_run_id, "status": "NOT_FOUND"}
    return _chat_run_to_api(record)


def get_conversation(conversation_id: str) -> dict[str, object]:
    conversation = conversation_repository.get(conversation_id)
    if conversation is None:
        return {"conversationId": conversation_id, "status": "NOT_FOUND", "items": []}
    runs = [
        _chat_run_to_api(run)
        for run in run_repository.list_chat_runs()
        if run["conversation_id"] == conversation_id
    ]
    return {
        "conversationId": conversation_id,
        "title": conversation.get("title"),
        "items": runs,
    }


def _chat_run_to_api(record: dict) -> dict[str, object]:
    return {
        "chatRunId": record["chat_run_id"],
        "conversationId": record["conversation_id"],
        "status": record["status"],
        "intent": record["intent"],
        "route": record["route"],
        "policyDecision": record["policy_decision"],
        "blockers": list(record.get("blockers", [])),
        "messageSummary": record["user_message_summary"],
        "pgptUsed": record.get("pgpt_used", False),
        "pgptModel": record.get("pgpt_model"),
        "pgptFallbackReason": record.get("pgpt_fallback_reason"),
        "pgptReasonSummary": record.get("pgpt_reason_summary"),
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_blockers(blockers: list[object]) -> list[str]:
    safe: list[str] = []
    for blocker in blockers:
        text = str(blocker)
        if find_redaction_violations(text):
            safe.append("REDACTED_POLICY_BLOCKER")
        else:
            safe.append(text)
    return safe
