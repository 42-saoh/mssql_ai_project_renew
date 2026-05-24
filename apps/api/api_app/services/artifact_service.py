from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.repositories import artifact_repository, validation_repository
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist, content_ref_for_artifact
from plf_agent_validation.policy_validator import validate_runtime_result


def list_artifacts() -> dict:
    return {"items": [to_api_artifact(record) for record in artifact_repository.list_all()]}


def get_artifact(artifact_id: str) -> dict:
    record = artifact_repository.get(artifact_id)
    if record is None:
        return {"artifactId": artifact_id, "status": "NOT_FOUND"}
    return to_api_artifact(record)


def persist_artifact_after_validation(proposal: dict, *, chat_run_id: str = "manual", codex_run_id: str | None = None) -> dict:
    result = {
        "productionReady": proposal.get("productionReady", False),
        "artifactProposals": [proposal],
    }
    ok, blockers = validate_runtime_result(result)
    if not ok:
        validation_id = f"validation_{uuid4().hex[:12]}"
        validation = validation_repository.put(
            validation_id,
            {
                "validation_id": validation_id,
                "artifact_id": "",
                "schema_valid": False,
                "policy_valid": False,
                "static_valid": False,
                "blocker_codes": blockers,
                "review_markers": proposal.get("reviewMarkers", []),
                "created_at": _now(),
            },
        )
        return {"status": "BLOCKED", "blockers": blockers, "validation": validation}

    artifact_id = f"artifact_{uuid4().hex[:12]}"
    content_markdown = str(proposal.get("contentMarkdown", ""))
    record = {
        "artifact_id": artifact_id,
        "chat_run_id": chat_run_id,
        "codex_run_id": codex_run_id,
        "artifact_type": proposal["artifactType"],
        "title": proposal["title"],
        "content_ref": content_ref_for_artifact(artifact_id),
        "content_hash": hashlib.sha256(content_markdown.encode("utf-8")).hexdigest(),
        "production_ready": False,
        "review_required": True,
        "evidence_refs": list(proposal.get("evidenceRefs", [])),
        "review_markers": list(proposal.get("reviewMarkers", [])),
        "created_at": _now(),
    }
    assert_safe_to_persist(record)
    artifact = artifact_repository.put(artifact_id, record)

    validation_id = f"validation_{uuid4().hex[:12]}"
    validation = validation_repository.put(
        validation_id,
        {
            "validation_id": validation_id,
            "artifact_id": artifact_id,
            "schema_valid": True,
            "policy_valid": True,
            "static_valid": True,
            "blocker_codes": [],
            "review_markers": record["review_markers"],
            "created_at": _now(),
        },
    )
    return {"status": "PERSISTED", "artifact": to_api_artifact(artifact), "validation": validation}


def to_api_artifact(record: dict) -> dict:
    return {
        "artifactId": record["artifact_id"],
        "artifactType": record["artifact_type"],
        "title": record["title"],
        "contentRef": record["content_ref"],
        "contentHash": record["content_hash"],
        "evidenceRefs": list(record.get("evidence_refs", [])),
        "reviewMarkers": list(record.get("review_markers", [])),
        "productionReady": False,
        "reviewRequired": True,
        "createdAt": record["created_at"],
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _stable_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
