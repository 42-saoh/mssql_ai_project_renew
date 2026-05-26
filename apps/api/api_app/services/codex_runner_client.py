from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.repositories import run_repository
from apps.api.api_app.services.observability_service import record_observability_event
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist
from plf_agent_contracts.policy import DEFAULT_RUNTIME_POLICY
from services.codex_runner.runner_app.fake_runner import run_fake


def submit_codex_run(request: dict) -> dict:
    codex_run_id = f"codexrun_{uuid4().hex[:12]}"
    target_key = _target_key(request)
    policy = _closed_runtime_policy(request)
    fake_result = run_fake(
        {
            "runType": request["runType"],
            "target": {"targetKey": target_key},
        }
    )
    target = request.get("target") if isinstance(request.get("target"), dict) else {}
    record = {
        "codex_run_id": codex_run_id,
        "chat_run_id": request["chatRunId"],
        "conversation_id": request["conversationId"],
        "run_type": request["runType"],
        "runner_mode": "fake",
        "runtime_profile": "runtime-readonly",
        "workspace_id": "pending",
        "status": "SUBMITTED",
        "output_schema_name": request.get("outputSchema", "service_codex_run_result.schema.json"),
        "validation_status": "PENDING",
        "target_key": target_key,
        "target_object_type": target.get("objectType"),
        "target_schema": target.get("schema"),
        "target_name": target.get("name"),
        "tool_mode": request.get("toolMode", "EVIDENCE_BUNDLE_ONLY"),
        "runtime_policy_flags_closed": True,
        "runtime_policy_flag_count": len(policy),
        "skill_allowlist": list(request.get("skillAllowlist", [])),
        "fake_runner_status": fake_result.get("status"),
        "fake_runner_proposal_count": len(fake_result.get("artifactProposals", [])),
        "fake_runner_blockers": list(fake_result.get("blockers", [])),
        "created_at": _now(),
        "completed_at": None,
    }
    assert_safe_to_persist(record)
    stored = run_repository.put_codex_run(codex_run_id, record)
    record_observability_event(
        "codex_run_submitted",
        subject_type="codex_run",
        subject_id=codex_run_id,
        codex_run_id=codex_run_id,
        chat_run_id=request["chatRunId"],
        conversation_id=request["conversationId"],
        run_type=str(request["runType"]),
        runner_mode="fake",
        status="SUBMITTED",
        validation_status="PENDING",
        target_key=target_key,
        blocker_codes=list(fake_result.get("blockers", [])),
        created_at=record["created_at"],
    )
    return {
        "status": "SUBMITTED",
        "codexRunId": codex_run_id,
        "record": stored,
        "fakeRunner": {
            "status": fake_result.get("status"),
            "proposalCount": len(fake_result.get("artifactProposals", [])),
        },
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _target_key(request: dict) -> str:
    target = request.get("target") if isinstance(request.get("target"), dict) else {}
    return str(request.get("targetKey") or target.get("targetKey") or "unresolved")


def _closed_runtime_policy(request: dict) -> dict[str, bool]:
    policy = request.get("policy")
    if policy is None:
        raise ValueError("Codex Runner request policy is required.")
    if not isinstance(policy, dict):
        raise ValueError("Codex Runner request policy must be an object.")
    closed_policy = {key: policy.get(key) for key in DEFAULT_RUNTIME_POLICY}
    if closed_policy != DEFAULT_RUNTIME_POLICY or set(policy) != set(DEFAULT_RUNTIME_POLICY):
        raise ValueError("Codex Runner request policy must keep all runtime flags false.")
    return dict(closed_policy)
