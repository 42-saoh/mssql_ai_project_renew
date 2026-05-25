from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "codex-strict-goal-runner.py"
SPEC = importlib.util.spec_from_file_location("codex_strict_goal_runner", SCRIPT)
assert SPEC is not None
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


def test_windows_codex_resolution_prefers_cmd_shim(monkeypatch):
    monkeypatch.setattr(runner, "is_windows", lambda: True)

    def fake_which(name: str) -> str | None:
        return {
            "codex": r"C:\Users\dev\AppData\Roaming\npm\codex",
            "codex.cmd": r"C:\Users\dev\AppData\Roaming\npm\codex.cmd",
        }.get(name)

    monkeypatch.setattr(runner.shutil, "which", fake_which)

    assert runner.resolve_codex_executable(None).endswith("codex.cmd")


def test_windows_codex_resolution_rejects_bare_npm_shim(monkeypatch):
    monkeypatch.setattr(runner, "is_windows", lambda: True)
    monkeypatch.setattr(runner.shutil, "which", lambda name: r"C:\npm\codex" if name == "codex" else None)

    with pytest.raises(SystemExit) as exc:
        runner.resolve_codex_executable(None)

    assert "codex.cmd" in str(exc.value)


def test_validation_shell_auto_uses_powershell_on_windows(monkeypatch):
    monkeypatch.setattr(runner, "is_windows", lambda: True)

    cmd = runner.build_validation_command("make test", "auto")

    assert cmd[:5] == ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass"]
    assert "make test" in cmd[-1]
    assert "LASTEXITCODE" in cmd[-1]


def test_validation_shell_auto_uses_bash_off_windows(monkeypatch):
    monkeypatch.setattr(runner, "is_windows", lambda: False)

    assert runner.build_validation_command("make test", "auto") == ["bash", "-lc", "make test"]


def test_validation_env_adds_explicit_python_make_and_path(tmp_path, monkeypatch):
    python_bin = tmp_path / "Python314" / "python.exe"
    make_bin = tmp_path / "Make" / "bin" / "make.exe"
    extra_dir = tmp_path / "tools"
    args = SimpleNamespace(
        validation_path_prepend=[str(extra_dir)],
        validation_python=str(python_bin),
        validation_make=str(make_bin),
    )
    monkeypatch.setenv("PATH", "C:\\Windows")

    env = runner.build_validation_env(args)
    path_parts = env["PATH"].split(runner.os.pathsep)

    assert env["PYTHON"] == str(python_bin)
    assert path_parts[:3] == [str(extra_dir), str(python_bin.parent), str(make_bin.parent)]


def test_stage_boundaries_match_goal_plan(tmp_path):
    goals = [tmp_path / "goals" / f"G{i:02d}-goal.md" for i in range(13)]

    assert [goal.name for goal in goals if runner.is_stage_boundary(goal)] == [
        "G02-goal.md",
        "G07-goal.md",
        "G10-goal.md",
        "G12-goal.md",
    ]
    assert [goal.name for goal in runner.goals_through_stage_boundary(goals, goals[7])] == [
        f"G{i:02d}-goal.md" for i in range(8)
    ]


def test_stage_validation_deduplicates_matching_commands(tmp_path, monkeypatch):
    goal_dir = tmp_path / "goals"
    goal_dir.mkdir()
    goals = []
    for i in range(3):
        goal = goal_dir / f"G{i:02d}-goal.md"
        goal.write_text("## Validation commands\n\n```bash\nmake test\n```\n", encoding="utf-8")
        goals.append(goal)

    calls = []

    def fake_run_command(cmd, cwd, log_path=None, input_text=None, env=None):
        calls.append(cmd)
        assert env is not None
        assert env["PYTHON"].endswith("python.exe")
        assert log_path is not None
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("ok\n", encoding="utf-8")
        return 0, "", ""

    monkeypatch.setattr(runner, "run_command", fake_run_command)
    args = SimpleNamespace(
        workspace=tmp_path,
        validation_shell="powershell",
        validation_path_prepend=[],
        validation_python=str(tmp_path / "Python314" / "python.exe"),
        validation_make=None,
    )

    ok, result = runner.run_stage_validation(
        "Foundation Complete",
        goals,
        args,
        tmp_path / ".codex-goals" / "runs" / "stage",
        "poststage-G02",
    )

    assert ok is True
    assert result is None
    assert len(calls) == 1
    assert "make test" in calls[0][-1]


def test_auto_commit_git_add_excludes_runner_state_dir(tmp_path):
    args = SimpleNamespace(workspace=tmp_path, state_dir=tmp_path / ".codex-goals")

    assert runner.build_git_add_command(args) == [
        "git",
        "add",
        "-A",
        "--",
        ".",
        ":(exclude).codex-goals/",
    ]


def test_execute_prompt_includes_last_failed_retry_context(tmp_path):
    workspace = tmp_path
    goals = [
        workspace / "goals" / "G00-legacy-reference-freeze.md",
        workspace / "goals" / "G01-greenfield-foundation-dual-codex-realm.md",
    ]
    retry_result = {
        "status": "fail",
        "earliest_failed_goal": "goals/G00-legacy-reference-freeze.md",
        "summary": "Preview-only artifact can be persisted.",
        "blockers": ["NON_PERSISTABLE_ARTIFACT_TYPE gate is missing"],
        "validation": "semantic verifier failed",
        "remaining_risks": ["rerun make test"],
    }

    prompt = runner.build_execute_prompt(goals[0], goals, 0, workspace, retry_result)

    assert "Current retry context from the most recent failed verifier or execution" in prompt
    assert "Preview-only artifact can be persisted." in prompt
    assert "NON_PERSISTABLE_ARTIFACT_TYPE gate is missing" in prompt
    assert 'address those blockers explicitly before returning "pass"' in prompt
    assert "You may strengthen the current goal file or previous goal files" in prompt
    assert "Do not edit later goal files" in prompt
    assert "Stage gates:" in prompt
    assert "Outer validation gates run only at stage boundaries G02, G07, G10, and G12" in prompt


def test_execute_prompt_requires_concrete_repair_for_previous_stage_regression(tmp_path):
    workspace = tmp_path
    goals = [workspace / "goals" / f"G{i:02d}-goal.md" for i in range(8)]
    retry_result = {
        "status": "fail",
        "earliest_failed_goal": "goals/G00-goal.md",
        "summary": "Foundation contract regressed during MVP gate.",
        "changed_files": [],
        "validation": "semantic verifier failed",
        "blockers": ["G00 no longer blocks procedure execution"],
        "remaining_risks": [],
        "confidence": 1,
    }
    runner.annotate_previous_stage_regression(retry_result, goals, 7, 0, "MVP Complete")

    prompt = runner.build_execute_prompt(goals[0], goals, 0, workspace, retry_result)

    assert "requires_concrete_repair: true" in prompt
    assert "completed previous stage regressed" in prompt
    assert "changed_files must include" in prompt


def test_concrete_repair_failure_result_rejects_empty_changed_files(tmp_path):
    goal_file = tmp_path / "goals" / "G00-goal.md"
    retry_result = {
        "_requires_concrete_repair": True,
        "_regressed_from_stage": "MVP Complete",
    }

    result = runner.concrete_repair_failure_result(goal_file, tmp_path, retry_result)

    assert result["status"] == "fail"
    assert result["_requires_concrete_repair"] is True
    assert "changed_files" in result["blockers"][0]


def test_run_validation_returns_failure_context_when_commands_are_missing(tmp_path):
    goal_dir = tmp_path / "goals"
    goal_dir.mkdir()
    goal_file = goal_dir / "G00-missing-validation.md"
    goal_file.write_text("# Missing validation\n\n## Validation commands\n", encoding="utf-8")
    args = SimpleNamespace(workspace=tmp_path, validation_shell="powershell")
    run_dir = tmp_path / ".codex-goals" / "runs" / "round-001-preverify-G00"

    ok, result = runner.run_validation(goal_file, args, run_dir, "preverify-G00")

    assert ok is False
    assert result is not None
    assert result["status"] == "fail"
    assert result["goal_file"].endswith("G00-missing-validation.md")
    assert result["earliest_failed_goal"] == result["goal_file"]
    assert "No validation commands found" in result["blockers"][0]
    assert "Validation log excerpt" in result["validation"]
    assert (run_dir / "preverify-G00.validation.missing.log").exists()


def test_run_validation_includes_failed_command_log_excerpt(tmp_path, monkeypatch):
    goal_dir = tmp_path / "goals"
    goal_dir.mkdir()
    goal_file = goal_dir / "G00-failing-validation.md"
    goal_file.write_text("## Validation commands\n\n```bash\nmake test\n```\n", encoding="utf-8")
    args = SimpleNamespace(workspace=tmp_path, validation_shell="powershell")
    run_dir = tmp_path / ".codex-goals" / "runs" / "round-001-preverify-G00"

    def fake_run_command(cmd, cwd, log_path=None, input_text=None, env=None):
        assert "make test" in cmd[-1]
        assert log_path is not None
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("validation failed because test_x failed\n", encoding="utf-8")
        return 7, "", ""

    monkeypatch.setattr(runner, "run_command", fake_run_command)

    ok, result = runner.run_validation(goal_file, args, run_dir, "preverify-G00")

    assert ok is False
    assert result is not None
    assert "Validation command failed with exit code 7: make test" in result["blockers"][0]
    assert "validation failed because test_x failed" in result["validation"]


def test_run_command_logs_oserror(tmp_path, monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("missing executable")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    log_path = tmp_path / "command.log"

    code, stdout, stderr = runner.run_command(["missing"], cwd=tmp_path, log_path=log_path)

    assert code == 127
    assert stdout == ""
    assert "FileNotFoundError" in stderr
    assert "--- exit_code ---\n127" in log_path.read_text(encoding="utf-8")


def test_run_command_uses_utf8_decoding_with_replacement(tmp_path, monkeypatch):
    captured = {}

    def fake_run(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="ok \u2014\n", stderr="warning\n")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    code, stdout, stderr = runner.run_command(["codex"], cwd=tmp_path)

    assert code == 0
    assert stdout == "ok \u2014\n"
    assert stderr == "warning\n"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_run_command_logs_empty_streams_when_subprocess_returns_none(tmp_path, monkeypatch):
    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=None, stderr=None)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    log_path = tmp_path / "command.log"

    code, stdout, stderr = runner.run_command(["codex"], cwd=tmp_path, log_path=log_path)

    assert code == 0
    assert stdout == ""
    assert stderr == ""
    log_text = log_path.read_text(encoding="utf-8")
    assert "--- stdout ---" in log_text
    assert "--- stderr ---" in log_text
    assert "--- exit_code ---\n0" in log_text
