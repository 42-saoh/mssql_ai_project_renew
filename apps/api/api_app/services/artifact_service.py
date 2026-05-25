from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from uuid import uuid4

from apps.api.api_app.repositories import artifact_repository, validation_repository
from apps.api.api_app.services.persistence_safety import assert_safe_to_persist, content_ref_for_artifact
from plf_agent_contracts.enums import ArtifactType
from plf_agent_validation.policy_validator import validate_runtime_result
from plf_agent_validation.redaction_validator import find_redaction_violations

PERSISTABLE_ARTIFACT_TYPES = {artifact_type.value for artifact_type in ArtifactType}
_SAFE_ARTIFACT_TYPE_LABELS = PERSISTABLE_ARTIFACT_TYPES | {
    "DDL_DRAFT",
    "MODEL_DRAFT",
    "TABLE_DESIGN_PREVIEW",
    "VO_DRAFT",
    "MISSING",
}
_SAFE_BLOCKER_CODE = re.compile(r"^[A-Za-z0-9_:$.\[\]-]+$")
_VALUE_BEARING_BLOCKER_PREFIXES = {
    "NON_PERSISTABLE_ARTIFACT_TYPE",
    "RETIRED_ARTIFACT_TYPE",
    "UNKNOWN_ARTIFACT_TYPE",
}
_JAVA_FILE_NAME_BLOCKER_PREFIX = "JAVA_MYBATIS_STATIC:MISSING_REVIEW_MARKER:"
_RUN_TYPE_BY_ARTIFACT_TYPE = {
    "SP_ANALYSIS_DOC": "SP_ANALYSIS",
    "DEPENDENCY_REPORT": "DEPENDENCY_ANALYSIS",
    "DTO_DRAFT": "DRAFT_GENERATION",
    "SERVICE_DRAFT": "DRAFT_GENERATION",
    "MAPPER_INTERFACE": "DRAFT_GENERATION",
    "MAPPER_XML": "DRAFT_GENERATION",
    "TABLE_DESIGN_PREVIEW": "TABLE_DESIGN",
}


def list_artifacts() -> dict:
    return {"items": [to_api_artifact(record) for record in artifact_repository.list_all()]}


def get_artifact(artifact_id: str) -> dict:
    record = artifact_repository.get(artifact_id)
    if record is None:
        return {"artifactId": artifact_id, "status": "NOT_FOUND"}
    return to_api_artifact(record, include_validations=True)


def list_artifact_validations(artifact_id: str) -> dict:
    return {
        "artifactId": artifact_id,
        "items": [
            to_api_validation(record)
            for record in validation_repository.list_for_artifact(artifact_id)
        ],
    }


def persist_validated_artifact_request(payload: dict) -> dict:
    proposal = payload.get("proposal")
    if not isinstance(proposal, dict):
        return _blocked_validation_response(["MISSING_ARTIFACT_PROPOSAL"])
    return persist_artifact_after_validation(
        proposal,
        chat_run_id=str(payload.get("chatRunId") or "manual"),
        codex_run_id=payload.get("codexRunId"),
    )


def persist_artifact_after_validation(proposal: dict, *, chat_run_id: str = "manual", codex_run_id: str | None = None) -> dict:
    result = _runtime_result_for_proposal(proposal, chat_run_id=chat_run_id)
    ok, blockers = validate_runtime_result(result)
    blockers.extend(_persistence_blockers(proposal))
    if not ok or blockers:
        safe_blockers = _safe_blocker_codes_for_validation(blockers)
        validation_id = f"validation_{uuid4().hex[:12]}"
        validation_record = {
            "validation_id": validation_id,
            "artifact_id": "",
            "schema_valid": False,
            "policy_valid": False,
            "static_valid": False,
            "blocker_codes": safe_blockers,
            "review_markers": [],
            "created_at": _now(),
        }
        assert_safe_to_persist(validation_record)
        validation = validation_repository.put(validation_id, validation_record)
        return {"status": "BLOCKED", "blockers": safe_blockers, "validation": to_api_validation(validation)}

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
    validation_record = {
        "validation_id": validation_id,
        "artifact_id": artifact_id,
        "schema_valid": True,
        "policy_valid": True,
        "static_valid": True,
        "blocker_codes": [],
        "review_markers": record["review_markers"],
        "created_at": _now(),
    }
    assert_safe_to_persist(validation_record)
    validation = validation_repository.put(validation_id, validation_record)
    return {
        "status": "PERSISTED",
        "artifact": to_api_artifact(artifact, include_validations=True),
        "validation": to_api_validation(validation),
    }


def _runtime_result_for_proposal(proposal: dict, *, chat_run_id: str) -> dict:
    artifact_type = _artifact_type_value(proposal.get("artifactType"))
    return {
        "schemaVersion": "ServiceCodexRunResult.v1",
        "runType": _RUN_TYPE_BY_ARTIFACT_TYPE.get(artifact_type, "DRAFT_GENERATION"),
        "targetKey": chat_run_id,
        "status": "REVIEW_REQUIRED",
        "productionReady": proposal.get("productionReady", False),
        "reviewRequired": True,
        "artifactProposals": [proposal],
        "blockers": [],
        "validation": {
            "schemaValid": True,
            "policyValid": True,
            "staticValidationPassed": True,
        },
    }


def _safe_blocker_codes_for_validation(blockers: list[object]) -> list[str]:
    safe_codes: list[str] = []
    for blocker in blockers:
        code = _safe_blocker_code(blocker)
        if code not in safe_codes:
            safe_codes.append(code)
    return safe_codes


def _safe_blocker_code(blocker: object) -> str:
    code = str(blocker)
    if find_redaction_violations(code):
        return "REDACTION_VIOLATION_BLOCKED"

    prefix, separator, suffix = code.partition(":")
    if separator and prefix in _VALUE_BEARING_BLOCKER_PREFIXES:
        if suffix in _SAFE_ARTIFACT_TYPE_LABELS:
            return code
        return prefix
    if code.startswith(_JAVA_FILE_NAME_BLOCKER_PREFIX):
        return _JAVA_FILE_NAME_BLOCKER_PREFIX.rstrip(":")

    if _SAFE_BLOCKER_CODE.fullmatch(code):
        return code
    return "UNSAFE_BLOCKER_CODE"


def _persistence_blockers(proposal: dict) -> list[str]:
    artifact_type = _artifact_type_value(proposal.get("artifactType"))
    if artifact_type not in PERSISTABLE_ARTIFACT_TYPES:
        return [f"NON_PERSISTABLE_ARTIFACT_TYPE:{artifact_type or 'MISSING'}"]
    return []


def _artifact_type_value(value: object) -> str:
    if isinstance(value, ArtifactType):
        return value.value
    if value is None:
        return ""
    return str(value)


def to_api_artifact(record: dict, *, include_validations: bool = False) -> dict:
    validations = [
        to_api_validation(validation)
        for validation in validation_repository.list_for_artifact(record["artifact_id"])
    ]
    latest_validation = validations[-1] if validations else None
    payload = {
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
    if latest_validation:
        payload["validationStatus"] = _validation_status(latest_validation)
        payload["validation"] = latest_validation
    else:
        payload["validationStatus"] = "PENDING"
    if include_validations:
        payload["validations"] = validations
    return payload


def to_api_validation(record: dict) -> dict:
    return {
        "validationId": record["validation_id"],
        "artifactId": record.get("artifact_id") or "",
        "schemaValid": bool(record.get("schema_valid", False)),
        "policyValid": bool(record.get("policy_valid", False)),
        "staticValid": bool(record.get("static_valid", False)),
        "blockerCodes": list(record.get("blocker_codes", [])),
        "reviewMarkers": list(record.get("review_markers", [])),
        "createdAt": record["created_at"],
    }


def _validation_status(validation: dict) -> str:
    if validation.get("blockerCodes"):
        return "BLOCKED"
    if validation.get("schemaValid") and validation.get("policyValid") and validation.get("staticValid"):
        return "VALIDATED"
    return "FAILED"


def _blocked_validation_response(blockers: list[str]) -> dict:
    safe_blockers = _safe_blocker_codes_for_validation(blockers)
    validation_id = f"validation_{uuid4().hex[:12]}"
    validation_record = {
        "validation_id": validation_id,
        "artifact_id": "",
        "schema_valid": False,
        "policy_valid": False,
        "static_valid": False,
        "blocker_codes": safe_blockers,
        "review_markers": [],
        "created_at": _now(),
    }
    assert_safe_to_persist(validation_record)
    validation = validation_repository.put(validation_id, validation_record)
    return {"status": "BLOCKED", "blockers": safe_blockers, "validation": to_api_validation(validation)}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _stable_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
