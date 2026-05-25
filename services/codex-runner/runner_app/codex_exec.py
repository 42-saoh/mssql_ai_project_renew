from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

DEFAULT_OUTPUT_SCHEMA = "schemas/output.schema.json"
DEFAULT_TIMEOUT_SECONDS = 600


class CodexExecCommandError(ValueError):
    """Raised when a codex exec command would leave the runtime workspace."""


def normalize_output_schema(output_schema: str | Path = DEFAULT_OUTPUT_SCHEMA) -> str:
    schema_path = Path(str(output_schema))
    if schema_path.is_absolute() or ".." in schema_path.parts:
        raise CodexExecCommandError("Output schema must be runtime-local")
    if len(schema_path.parts) == 1:
        schema_path = Path("schemas") / schema_path
    if schema_path.parts[0] != "schemas" or schema_path.suffix != ".json":
        raise CodexExecCommandError("Output schema must be a JSON file under schemas/")
    return schema_path.as_posix()


def build_codex_exec_command(workspace: str | Path, output_schema: str | Path = DEFAULT_OUTPUT_SCHEMA) -> list[str]:
    schema = normalize_output_schema(output_schema)
    return [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--model",
        "gpt-5.5",
        "-c",
        'model_reasoning_effort="xhigh"',
        "--ask-for-approval",
        "never",
        "--sandbox",
        "read-only",
        "--json",
        "--output-last-message",
        "outputs/final.json",
        "--output-schema",
        schema,
        "Read AGENTS.md, input/run_request.json, input/evidence_bundle.json, and produce only schema-valid final JSON.",
    ]


def run_codex_exec(
    workspace: str | Path,
    output_schema: str | Path = DEFAULT_OUTPUT_SCHEMA,
    *,
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    command = build_codex_exec_command(workspace, output_schema)
    runner = run_command or subprocess.run
    return runner(command, check=False, text=True, capture_output=True, timeout=timeout_seconds)
