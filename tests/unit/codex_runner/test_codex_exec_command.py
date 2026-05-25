from pathlib import Path

import pytest

from runner_app.codex_exec import CodexExecCommandError, build_codex_exec_command, normalize_output_schema, run_codex_exec
from runner_app.workspace import WorkspaceContractError

ROOT = Path(__file__).resolve().parents[3]


def test_codex_exec_command_is_bound_to_runtime_workspace_and_readonly():
    cmd = build_codex_exec_command("runtime-workspace")

    assert cmd[:2] == ["codex", "exec"]
    assert cmd[cmd.index("--cd") + 1] == "runtime-workspace"
    assert cmd[cmd.index("--model") + 1] == "gpt-5.5"
    assert cmd[cmd.index("--ask-for-approval") + 1] == "never"
    assert cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert "--json" in cmd
    assert cmd[cmd.index("--output-last-message") + 1] == "outputs/final.json"
    assert cmd[cmd.index("--output-schema") + 1] == "schemas/output.schema.json"

    instruction = cmd[-1]
    assert "Read AGENTS.md" in instruction
    assert "input/run_request.json" in instruction
    assert "input/evidence_bundle.json" in instruction
    assert "root" not in instruction.lower()


def test_codex_exec_command_allows_explicit_runtime_schema_override():
    cmd = build_codex_exec_command("runtime-workspace", "schemas/service_codex_run_result.schema.json")

    assert cmd[cmd.index("--output-schema") + 1] == "schemas/service_codex_run_result.schema.json"


def test_codex_exec_command_normalizes_bare_runtime_schema_name():
    assert normalize_output_schema("service_codex_run_result.schema.json") == "schemas/service_codex_run_result.schema.json"


@pytest.mark.parametrize(
    "output_schema",
    [
        "../service_codex_run_result.schema.json",
        "outside/service_codex_run_result.schema.json",
        "schemas/output.txt",
    ],
)
def test_codex_exec_command_rejects_schema_paths_outside_runtime_schemas(output_schema):
    with pytest.raises(CodexExecCommandError):
        normalize_output_schema(output_schema)


def test_run_codex_exec_rejects_development_root_before_runner_called():
    called = False

    def fake_runner(command, **kwargs):
        nonlocal called
        called = True

    with pytest.raises(WorkspaceContractError):
        run_codex_exec(ROOT, run_command=fake_runner)

    assert called is False
