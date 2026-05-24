from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.repositories import run_repository
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist


def submit_codex_run(request: dict) -> dict:
    codex_run_id = f"codexrun_{uuid4().hex[:12]}"
    record = {
        "codex_run_id": codex_run_id,
        "chat_run_id": request["chatRunId"],
        "conversation_id": request["conversationId"],
        "run_type": request["runType"],
        "runtime_profile": "runtime-readonly",
        "workspace_id": "pending",
        "status": "SUBMITTED",
        "output_schema_name": "service_codex_run_result.schema.json",
        "validation_status": "PENDING",
        "target_key": request.get("targetKey", "unresolved"),
        "created_at": _now(),
        "completed_at": None,
    }
    assert_safe_to_persist(record)
    stored = run_repository.put_codex_run(codex_run_id, record)
    return {"status": "SUBMITTED", "codexRunId": codex_run_id, "record": stored}


def _now() -> str:
    return datetime.now(UTC).isoformat()
