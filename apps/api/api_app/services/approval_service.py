from __future__ import annotations

from datetime import UTC, datetime

from apps.api.api_app.repositories import approval_repository
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist


def resume_approval(approval_id: str) -> dict[str, object]:
    record = approval_repository.get(approval_id)
    if record is None:
        return {"approvalId": approval_id, "status": "NOT_FOUND"}
    record["status"] = "RESUMED"
    record["resolved_at"] = datetime.now(UTC).isoformat()
    assert_safe_to_persist(record)
    approval_repository.put(approval_id, record)
    return {"approvalId": approval_id, "status": "RESUMED"}
