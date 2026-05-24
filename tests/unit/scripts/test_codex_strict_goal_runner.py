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
