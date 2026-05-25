from __future__ import annotations

from datetime import UTC, datetime

from apps.api.api_app.repositories import approval_repository
from apps.api.api_app.services.observability_service import record_observability_event
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist


def list_approvals() -> dict[str, object]:
    return {"items": [to_api_approval(record) for record in approval_repository.list_all()]}


def get_approval(approval_id: str) -> dict[str, object]:
    record = approval_repository.get(approval_id)
    if record is None:
        return {"approvalId": approval_id, "status": "NOT_FOUND"}
    return to_api_approval(record)


def resume_approval(approval_id: str) -> dict[str, object]:
    record = approval_repository.get(approval_id)
    if record is None:
        return {"approvalId": approval_id, "status": "NOT_FOUND"}
    record["status"] = "RESUMED"
    resolved_at = datetime.now(UTC).isoformat()
    record["resolved_at"] = resolved_at
    assert_safe_to_persist(record)
    approval_repository.put(approval_id, record)
    record_observability_event(
        "approval_resumed",
        subject_type="approval",
        subject_id=approval_id,
        approval_id=approval_id,
        approval_type=str(record["approval_type"]),
        chat_run_id=str(record["chat_run_id"]),
        status="RESUMED",
        created_at=resolved_at,
    )
    return {"approvalId": approval_id, "status": "RESUMED"}


def to_api_approval(record: dict) -> dict[str, object]:
    return {
        "approvalId": record["approval_id"],
        "chatRunId": record["chat_run_id"],
        "approvalType": record["approval_type"],
        "status": record["status"],
        "reason": record["reason"],
        "requestedAt": record["requested_at"],
        "resolvedAt": record.get("resolved_at"),
    }
