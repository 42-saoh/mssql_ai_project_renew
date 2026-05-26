from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.auth import require_actor_id
from apps.api.api_app.repositories import approval_repository, conversation_repository, run_repository
from apps.api.api_app.services import metadata_service
from apps.api.api_app.services.codex_runner_client import submit_codex_run
from apps.api.api_app.services.observability_service import record_observability_event
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist, summarize_user_message
from plf_agent_contracts.codex_runner import ServiceCodexRunRequest, TargetRef
from plf_agent_orchestration.forbidden_operations import detect_forbidden_operation_blockers
from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_orchestration.state import safe_checkpoint_from_state
from plf_agent_validation.redaction_validator import find_redaction_violations

_RUNNER_INTENT_CONFIG = {
    "SP_ANALYSIS": {
        "object_type": "PROCEDURE",
        "output_schema": "schemas/sp_analysis_result.schema.json",
        "skills": ["runtime-sp-analysis", "runtime-output-validation", "runtime-policy-review"],
    },
    "DEPENDENCY_ANALYSIS": {
        "object_type": "OBJECT",
        "output_schema": "schemas/dependency_analysis_result.schema.json",
        "skills": ["runtime-dependency-analysis", "runtime-output-validation", "runtime-policy-review"],
    },
    "TABLE_DESIGN": {
        "object_type": "TABLE",
        "output_schema": "schemas/table_design_preview.schema.json",
        "skills": ["runtime-table-design-preview", "runtime-output-validation", "runtime-policy-review"],
    },
    "DRAFT_GENERATION": {
        "object_type": "OBJECT",
        "output_schema": "schemas/java_mybatis_draft_pack.schema.json",
        "skills": ["runtime-java-mybatis-draft", "runtime-output-validation", "runtime-policy-review"],
    },
}

_DOTTED_OBJECT_PATTERN = re.compile(
    r"\b(?:(?P<db>[A-Za-z][A-Za-z0-9_-]{0,63})\.)?"
    r"(?P<schema>[A-Za-z_][A-Za-z0-9_$#@]{0,127})\."
    r"(?P<name>[A-Za-z_][A-Za-z0-9_$#@]{0,127})\b"
)
_REDACTION_BLOCKER_CODES = {
    "CONNECTION_STRING",
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "RAW_SP",
    "ROW_DATA",
    "SECRET",
}
_PRE_ROUTE_REDACTION_BLOCKER_CODES = {
    "CONNECTION_STRING",
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "RAW_SP",
    "SECRET",
}


def create_chat_run(message: str, *, conversation_id: str | None = None, actor_id: str | None = None) -> dict[str, object]:
    actor = require_actor_id(actor_id)
    conversation_id = conversation_id or f"conv_{uuid4().hex[:12]}"
    chat_run_id = f"chatrun_{uuid4().hex[:12]}"
    routed = _pre_route_redaction_gate(
        message,
        conversation_id=conversation_id,
        chat_run_id=chat_run_id,
    ) or orchestrate_message(
        message,
        conversation_id=conversation_id,
        chat_run_id=chat_run_id,
    )
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
        "orchestrator_checkpoint": routed.get("checkpoint"),
        "created_at": now,
        "completed_at": now if status == "BLOCKED" else None,
    }
    assert_safe_to_persist(run_record)
    run_repository.put_chat_run(chat_run_id, run_record)
    record_observability_event(
        "chat_run_recorded",
        subject_type="chat_run",
        subject_id=chat_run_id,
        chat_run_id=chat_run_id,
        conversation_id=conversation_id,
        actor_id=actor,
        intent=str(routed["intent"]),
        route=str(routed["route"]),
        status=status,
        policy_decision=str(routed["policyDecision"]),
        blocker_codes=run_record["blockers"],
        created_at=now,
    )

    response: dict[str, object] = {
        "chatRunId": chat_run_id,
        "conversationId": conversation_id,
        "status": status,
        **routed,
    }

    if routed["route"] == "codex_runner" and routed["policyDecision"] == "ALLOW":
        codex_run = submit_codex_run(_runner_request_for_gateway(routed, chat_run_id, conversation_id, message))
        response["codexRunId"] = codex_run["codexRunId"]
        response["fakeRunner"] = codex_run.get("fakeRunner")

    if routed["route"] == "metadata_gateway" and routed["policyDecision"] == "ALLOW":
        response["metadataSearch"] = _metadata_search_for_gateway(message)

    if routed["route"] == "history_store" and routed["policyDecision"] == "ALLOW":
        response["historyLookup"] = _history_lookup_for_conversation(
            conversation_id,
            exclude_chat_run_id=chat_run_id,
        )

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
        record_observability_event(
            "approval_requested",
            subject_type="approval",
            subject_id=approval_id,
            approval_id=approval_id,
            approval_type="POLICY_REVIEW",
            chat_run_id=chat_run_id,
            status="PENDING",
            created_at=now,
        )
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


def list_conversations() -> dict[str, object]:
    runs = run_repository.list_chat_runs()
    items = []
    for conversation in conversation_repository.list_all():
        conversation_id = conversation["conversation_id"]
        items.append(
            {
                "conversationId": conversation_id,
                "title": conversation.get("title"),
                "createdAt": conversation.get("created_at"),
                "updatedAt": conversation.get("updated_at"),
                "runCount": sum(
                    1
                    for run in runs
                    if run.get("conversation_id") == conversation_id
                ),
            }
        )
    return {"items": items}


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
        "checkpoint": record.get("orchestrator_checkpoint"),
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_blockers(blockers: list[object]) -> list[str]:
    safe: list[str] = []
    for blocker in blockers:
        text = str(blocker)
        if text in _REDACTION_BLOCKER_CODES or find_redaction_violations(text):
            safe_code = "REDACTION_VIOLATION_BLOCKED"
        else:
            safe_code = text
        if safe_code not in safe:
            safe.append(safe_code)
    return safe


def _pre_route_redaction_gate(
    message: str,
    *,
    conversation_id: str,
    chat_run_id: str,
) -> dict[str, object] | None:
    redaction_blockers = [
        code
        for code in find_redaction_violations(message)
        if code in _PRE_ROUTE_REDACTION_BLOCKER_CODES
    ]
    if not redaction_blockers:
        return None

    blockers = _dedupe(detect_forbidden_operation_blockers(message) or redaction_blockers)
    checkpoint = safe_checkpoint_from_state(
        {
            "schemaVersion": "OrchestratorState.v1",
            "conversationId": conversation_id,
            "chatRunId": chat_run_id,
            "sanitizedMessageSummary": "Sanitized DB analysis request.",
            "intent": "BLOCKED_OR_APPROVAL_REQUIRED",
            "policyDecision": "BLOCKED",
            "blockers": blockers,
            "route": "blocked",
            "artifactIds": [],
            "reviewMarkers": [],
            "pgptUsed": False,
            "pgptFallbackReason": "POLICY_BLOCKED_BEFORE_PGPT",
            "steps": ["pre_route_redaction_gate"],
        }
    )
    return {
        "intent": "BLOCKED_OR_APPROVAL_REQUIRED",
        "policyDecision": "BLOCKED",
        "blockers": blockers,
        "route": "blocked",
        "pgptUsed": False,
        "pgptModel": None,
        "pgptFallbackReason": "POLICY_BLOCKED_BEFORE_PGPT",
        "pgptReasonSummary": None,
        "runnerRequest": None,
        "checkpoint": checkpoint,
        "orchestrator": {
            "engine": "service_pre_route",
            "checkpoint": "service_boundary",
            "nodes": ["pre_route_redaction_gate"],
        },
    }


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _runner_request_for_gateway(
    routed: dict[str, object],
    chat_run_id: str,
    conversation_id: str,
    message: str,
) -> dict[str, object]:
    runner_request = routed.get("runnerRequest")
    run_type = str(runner_request.get("runType") if isinstance(runner_request, dict) else routed["intent"])
    config = _RUNNER_INTENT_CONFIG.get(run_type, _RUNNER_INTENT_CONFIG["SP_ANALYSIS"])
    target = _target_ref_for_runner(message, object_type=config["object_type"])
    request = ServiceCodexRunRequest(
        runType=run_type,
        chatRunId=chat_run_id,
        conversationId=conversation_id,
        target=target,
        skillAllowlist=list(config["skills"]),
        outputSchema=str(config["output_schema"]),
    ).to_dict()
    return {key: value for key, value in request.items() if value is not None}


def _metadata_search_for_gateway(message: str) -> dict[str, object]:
    return metadata_service.search_metadata(message, db_profile_id="master", limit=20)


def _history_lookup_for_conversation(conversation_id: str, *, exclude_chat_run_id: str) -> dict[str, object]:
    items = [
        _chat_run_to_api(run)
        for run in run_repository.list_chat_runs()
        if run["conversation_id"] == conversation_id and run["chat_run_id"] != exclude_chat_run_id
    ]
    return {
        "source": "history_store",
        "items": items,
    }


def _target_ref_for_runner(message: str, *, object_type: str) -> TargetRef:
    match = _DOTTED_OBJECT_PATTERN.search(message or "")
    db_profile_id = "master"
    schema = "dbo"
    name = "unresolved"
    if match:
        db_profile_id = match.group("db") or db_profile_id
        schema = match.group("schema")
        name = match.group("name")
    target_key = f"{db_profile_id}.{object_type}.{schema}.{name}"
    return TargetRef(
        dbProfileId=db_profile_id,
        objectType=object_type,
        schema=schema,
        name=name,
        targetKey=target_key,
    )
