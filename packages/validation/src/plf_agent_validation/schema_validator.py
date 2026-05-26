from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_RUNNER_REQUEST_SCHEMA = "spec/codex-runner/service_codex_run_request.schema.json"
_RUNNER_RESULT_SCHEMA = "spec/codex-runner/service_codex_run_result.schema.json"
_ARTIFACT_SCHEMA_BY_TYPE = {
    "SP_ANALYSIS_DOC": "spec/artifacts/sp_analysis_doc.schema.json",
    "DEPENDENCY_REPORT": "spec/artifacts/dependency_report.schema.json",
    "DTO_DRAFT": "spec/artifacts/java_mybatis_draft_pack.schema.json",
    "SERVICE_DRAFT": "spec/artifacts/java_mybatis_draft_pack.schema.json",
    "MAPPER_INTERFACE": "spec/artifacts/java_mybatis_draft_pack.schema.json",
    "MAPPER_XML": "spec/artifacts/java_mybatis_draft_pack.schema.json",
    "TABLE_DESIGN_PREVIEW": "spec/artifacts/table_design_preview.schema.json",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_required_keys(obj: dict[str, Any], required: list[str]) -> tuple[bool, list[str]]:
    missing = [key for key in required if key not in obj]
    return not missing, missing


def validate_runner_result_schema(result: Any) -> list[str]:
    return _validate_schema(result, _RUNNER_RESULT_SCHEMA, "RUNNER_RESULT_SCHEMA_INVALID")


def validate_runner_request_schema(request: Any) -> list[str]:
    return _validate_schema(request, _RUNNER_REQUEST_SCHEMA, "RUNNER_REQUEST_SCHEMA_INVALID")


def validate_artifact_proposal_schema(proposal: Any) -> list[str]:
    if not isinstance(proposal, dict):
        return ["ARTIFACT_SCHEMA_INVALID:$:type"]
    artifact_type = str(proposal.get("artifactType") or "")
    schema_path = _ARTIFACT_SCHEMA_BY_TYPE.get(artifact_type)
    if not schema_path:
        artifact_type_code = "MISSING" if not artifact_type else "UNKNOWN_ARTIFACT_TYPE"
        return [f"ARTIFACT_SCHEMA_INVALID:{artifact_type_code}:artifactType:enum"]
    return _validate_schema(proposal, schema_path, "ARTIFACT_SCHEMA_INVALID")


def _validate_schema(payload: Any, rel_schema_path: str, code: str) -> list[str]:
    validator = _validator(rel_schema_path)
    return [
        f"{code}:{_json_path(error.absolute_path)}:{_validator_detail(error)}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    ]


@lru_cache(maxsize=None)
def _validator(rel_schema_path: str) -> Draft202012Validator:
    return Draft202012Validator(load_json(_repo_root() / rel_schema_path))


@lru_cache(maxsize=1)
def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "spec").is_dir() and (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _validator_detail(error: Any) -> str:
    if error.validator == "required":
        match = re.match(r"'([^']+)' is a required property", error.message)
        if match:
            return f"required:{match.group(1)}"
    return str(error.validator)
