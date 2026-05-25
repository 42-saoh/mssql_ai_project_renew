from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from plf_agent_validation.redaction_validator import contains_any_violation
from plf_agent_validation.schema_validator import validate_runner_request_schema

from .codex_exec import CodexExecCommandError, normalize_output_schema, run_codex_exec
from .event_parser import summarize_event_stream
from .sanitizer import safe_blocked_result, sanitize_result
from .validator import mark_validated
from .workspace import WorkspaceContractError, cleanup_workspace, create_workspace, write_run_inputs

DEFAULT_RUNTIME_TEMPLATE = Path(__file__).resolve().parents[1] / "runtime-template"
DEFAULT_WORKSPACE_BASE = Path(tempfile.gettempdir()) / "plf_codex_runner_workspaces"


@dataclass(frozen=True)
class RealRunnerConfig:
    workspace_base: str | Path = DEFAULT_WORKSPACE_BASE
    runtime_template: str | Path = DEFAULT_RUNTIME_TEMPLATE
    cleanup: bool = True
    timeout_seconds: int = 600


def run_real(workspace: str | Path) -> subprocess.CompletedProcess[str]:
    return run_codex_exec(workspace)


def submit_real_run(
    request: dict[str, Any],
    evidence_bundle: dict[str, Any] | None = None,
    *,
    tool_catalog: dict[str, Any] | None = None,
    config: RealRunnerConfig | None = None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    config = config or RealRunnerConfig()
    input_blockers = _input_blockers(request, evidence_bundle, tool_catalog)
    if input_blockers:
        return safe_blocked_result(request, input_blockers)

    try:
        output_schema = normalize_output_schema(request.get("outputSchema", "service_codex_run_result.schema.json"))
    except CodexExecCommandError as exc:
        return safe_blocked_result(request, [f"OUTPUT_SCHEMA_BLOCKED:{exc}"])

    workspace: Path | None = None
    runtime: dict[str, Any] = {}
    try:
        workspace = create_workspace(config.workspace_base, config.runtime_template)
        runtime["workspaceId"] = workspace.name
        write_run_inputs(workspace, request, evidence_bundle, tool_catalog)

        completed = run_codex_exec(workspace, output_schema, run_command=run_command, timeout_seconds=config.timeout_seconds)
        runtime.update(summarize_event_stream(completed.stdout or "", completed.stderr or ""))
        runtime["returnCode"] = completed.returncode
        if completed.returncode != 0:
            return safe_blocked_result(
                request,
                ["CODEX_EXEC_FAILED"],
                validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
                runtime=runtime,
            )

        final_path = workspace / "outputs" / "final.json"
        if not final_path.is_file():
            return safe_blocked_result(
                request,
                ["MISSING_FINAL_OUTPUT"],
                validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
                runtime=runtime,
            )

        try:
            result = json.loads(final_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return safe_blocked_result(
                request,
                ["FINAL_OUTPUT_JSON_INVALID"],
                validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
                runtime=runtime,
            )

        sanitized, violations = sanitize_result(result, request)
        if violations:
            sanitized["runtime"] = runtime
            return sanitized

        validated, blockers = mark_validated(sanitized)
        if blockers:
            return safe_blocked_result(
                request,
                blockers,
                validation=validated["validation"],
                runtime=runtime,
            )
        validated["runtime"] = runtime
        return validated
    except WorkspaceContractError:
        return safe_blocked_result(
            request,
            ["WORKSPACE_CONTRACT_BLOCKED"],
            validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
            runtime=runtime,
        )
    except subprocess.TimeoutExpired:
        return safe_blocked_result(
            request,
            ["CODEX_EXEC_TIMEOUT"],
            validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
            runtime=runtime,
        )
    except OSError:
        return safe_blocked_result(
            request,
            ["CODEX_EXEC_ERROR"],
            validation={"schemaValid": False, "policyValid": True, "staticValidationPassed": False},
            runtime=runtime,
        )
    finally:
        if workspace is not None and config.cleanup:
            cleanup_workspace(workspace)


def _input_blockers(
    request: dict[str, Any],
    evidence_bundle: dict[str, Any] | None,
    tool_catalog: dict[str, Any] | None,
) -> list[str]:
    blockers = validate_runner_request_schema(request)
    policy = request.get("policy") if isinstance(request.get("policy"), dict) else {}
    for key, value in policy.items():
        if key.startswith("allow") and value is not False:
            blockers.append(f"RUNNER_POLICY_ALLOWS_BLOCKED_OPERATION:{key}")
    for skill in request.get("skillAllowlist", []):
        if not str(skill).startswith("runtime-"):
            blockers.append(f"NON_RUNTIME_SKILL_BLOCKED:{skill}")

    request_for_redaction = {key: value for key, value in request.items() if key != "policy"}
    serialized_parts = [
        json.dumps(payload, ensure_ascii=False, default=str)
        for payload in (request_for_redaction, evidence_bundle or {}, tool_catalog or {})
    ]
    blockers.extend(contains_any_violation(serialized_parts))
    return _dedupe(blockers)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped
