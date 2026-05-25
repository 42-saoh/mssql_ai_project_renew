from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

RUNTIME_MARKER = "Service Codex Runner Realm"
RUNTIME_REQUIRED_PATHS = (
    "AGENTS.md",
    "POLICY.md",
    ".codex/config.toml",
    ".agents/skills",
    "schemas/output.schema.json",
)
WORKSPACE_REQUIRED_DIRS = ("input", "outputs", "scratch")
FORBIDDEN_COPIED_FROM_ROOT = (
    ".env",
    ".env.example",
    "DESIGN.md",
    "README.md",
    "goals",
    "docs/reference",
)


class WorkspaceContractError(ValueError):
    """Raised when a runner workspace would cross the runtime boundary."""


def create_workspace(base_dir: str | Path, runtime_template: str | Path) -> Path:
    base = Path(base_dir).resolve()
    template = _resolve_runtime_template(runtime_template)
    base.mkdir(parents=True, exist_ok=True)
    workspace = base / f"codexrun_{uuid4().hex}"
    _assert_no_symlinks(template)
    shutil.copytree(template, workspace, symlinks=True)
    for dirname in WORKSPACE_REQUIRED_DIRS:
        (workspace / dirname).mkdir(exist_ok=True)
    _assert_workspace_contract(workspace)
    return workspace


def write_run_inputs(
    workspace: str | Path,
    request: dict[str, Any],
    evidence_bundle: dict[str, Any] | None = None,
    tool_catalog: dict[str, Any] | None = None,
) -> None:
    workspace_path = assert_runtime_workspace(workspace)
    input_dir = workspace_path / "input"
    _write_json(input_dir / "run_request.json", request)
    _write_json(input_dir / "evidence_bundle.json", evidence_bundle or {})
    if tool_catalog is not None:
        _write_json(input_dir / "tool_catalog.json", tool_catalog)


def cleanup_workspace(path: str | Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def assert_runtime_workspace(workspace: str | Path) -> Path:
    workspace_path = Path(workspace).resolve()
    _assert_workspace_contract(workspace_path)
    _assert_no_symlinks(workspace_path)
    return workspace_path


def _resolve_runtime_template(runtime_template: str | Path) -> Path:
    template = Path(runtime_template).resolve()
    if not template.is_dir():
        raise WorkspaceContractError(f"Runtime template does not exist: {template}")

    missing = [rel for rel in RUNTIME_REQUIRED_PATHS if not (template / rel).exists()]
    if missing:
        raise WorkspaceContractError(f"Runtime template missing required paths: {missing}")

    agent_text = (template / "AGENTS.md").read_text(encoding="utf-8")
    if RUNTIME_MARKER not in agent_text:
        raise WorkspaceContractError("Runtime template AGENTS.md is not Service Codex Runner scoped")

    for forbidden in FORBIDDEN_COPIED_FROM_ROOT:
        if (template / forbidden).exists():
            raise WorkspaceContractError(f"Runtime template contains forbidden root material: {forbidden}")

    return template


def _assert_workspace_contract(workspace: Path) -> None:
    if not workspace.is_dir():
        raise WorkspaceContractError(f"Workspace does not exist: {workspace}")
    for dirname in WORKSPACE_REQUIRED_DIRS:
        if not (workspace / dirname).is_dir():
            raise WorkspaceContractError(f"Workspace missing required directory: {dirname}")
    for required in RUNTIME_REQUIRED_PATHS:
        if not (workspace / required).exists():
            raise WorkspaceContractError(f"Workspace missing runtime path: {required}")
    for forbidden in FORBIDDEN_COPIED_FROM_ROOT:
        if (workspace / forbidden).exists():
            raise WorkspaceContractError(f"Workspace contains forbidden root material: {forbidden}")


def _assert_no_symlinks(path: Path) -> None:
    for child in path.rglob("*"):
        if child.is_symlink():
            raise WorkspaceContractError(f"Runtime template symlink is not allowed: {child}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
