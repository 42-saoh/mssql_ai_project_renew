#!/usr/bin/env python3
"""
Strict sequential Codex goal runner.

What it enforces:
1. Goal files are executed in lexical order: goals/G00..., G01..., G02...
2. Only one goal is given to Codex per run.
3. Validation gates run only at named stage boundaries: G02, G07, G10, and G12.
4. If a previous goal fails validation or semantic verification, all later goals are marked pending
   and execution returns to the earliest failing goal.
5. Results, prompts, validation logs, and state are stored under .codex-goals/.

Requirements:
- Python 3.9+
- Codex CLI installed and authenticated
- Run from inside a Git repository unless you pass --skip-git-repo-check
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


STATUS_PENDING = "pending"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_BLOCKED = "blocked"

STAGE_DEFINITIONS: List[Tuple[str, int, int]] = [
    ("Foundation Complete", 0, 2),
    ("MVP Complete", 3, 7),
    ("Feature Complete", 8, 10),
    ("Release Complete", 11, 12),
]

GENERATED_CHANGE_PREFIXES = (
    ".codex-goals/",
    ".git/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
)
CONCRETE_REPAIR_PREFIXES = (
    "apps/",
    "db/",
    "goals/",
    "packages/",
    "scripts/",
    "services/",
    "spec/",
    "tests/",
)


RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["pass", "fail", "blocked"]},
        "goal_file": {"type": "string"},
        "earliest_failed_goal": {"type": ["string", "null"]},
        "summary": {"type": "string"},
        "changed_files": {"type": "array", "items": {"type": "string"}},
        "validation": {"type": "string"},
        "blockers": {"type": "array", "items": {"type": "string"}},
        "remaining_risks": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "status",
        "goal_file",
        "earliest_failed_goal",
        "summary",
        "changed_files",
        "validation",
        "blockers",
        "remaining_risks",
        "confidence",
    ],
    "additionalProperties": False,
}


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def print_step(message: str) -> None:
    print(f"\n[goal-runner] {message}", flush=True)


def is_windows() -> bool:
    return os.name == "nt"


def format_command_for_log(cmd: List[str]) -> str:
    if is_windows():
        return subprocess.list2cmdline(cmd)
    return " ".join(shlex.quote(c) for c in cmd)


def build_git_command(workspace: Path, args: List[str]) -> List[str]:
    return ["git", "-c", f"safe.directory={workspace.resolve().as_posix()}", *args]


def run_command(
    cmd: List[str],
    cwd: Path,
    log_path: Optional[Path] = None,
    input_text: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        returncode = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except OSError as exc:
        returncode = 127 if isinstance(exc, FileNotFoundError) else 126
        stdout = ""
        stderr = f"{type(exc).__name__}: {exc}\n"

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as f:
            f.write("$ " + format_command_for_log(cmd) + "\n\n")
            if input_text:
                f.write("--- stdin ---\n")
                f.write(input_text)
                if not input_text.endswith("\n"):
                    f.write("\n")
                f.write("\n")
            f.write("--- stdout ---\n")
            f.write(stdout)
            if not stdout.endswith("\n"):
                f.write("\n")
            f.write("\n--- stderr ---\n")
            f.write(stderr)
            if not stderr.endswith("\n"):
                f.write("\n")
            f.write(f"\n--- exit_code ---\n{returncode}\n")
    return returncode, stdout, stderr


def resolve_codex_executable(explicit: Optional[str]) -> str:
    if explicit:
        resolved = shutil.which(explicit) or explicit
        if is_windows() and Path(resolved).suffix.lower() not in {".bat", ".cmd", ".com", ".exe"}:
            raise SystemExit(
                f"Codex executable is not directly runnable by Windows Python: {resolved}. "
                "Pass --codex-bin codex.cmd or put codex.cmd on PATH."
            )
        return resolved

    if is_windows():
        for name in ("codex.cmd", "codex.exe", "codex.bat"):
            resolved = shutil.which(name)
            if resolved:
                return resolved
        bare = shutil.which("codex")
        if bare:
            raise SystemExit(
                f"Only a non-Windows Codex shim was found: {bare}. "
                "Put codex.cmd on PATH or pass --codex-bin codex.cmd."
            )
    else:
        resolved = shutil.which("codex")
        if resolved:
            return resolved

    raise SystemExit("codex CLI was not found on PATH. Install it first: npm i -g @openai/codex")


def ensure_codex(explicit: Optional[str]) -> str:
    return resolve_codex_executable(explicit)


def ensure_git_repo(workspace: Path, skip: bool) -> None:
    if skip:
        return
    code, _, _ = run_command(build_git_command(workspace, ["rev-parse", "--is-inside-work-tree"]), cwd=workspace)
    if code != 0:
        raise SystemExit(
            "This runner should be used inside a Git repository. "
            "Run from the repo root or pass --skip-git-repo-check if you intentionally want to bypass this."
        )


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def discover_goals(goals_dir: Path) -> List[Path]:
    if not goals_dir.exists():
        raise SystemExit(f"Goals directory not found: {goals_dir}")
    goals = sorted(p for p in goals_dir.glob("G*.md") if p.is_file())
    if not goals:
        raise SystemExit(f"No goal files matching G*.md found in: {goals_dir}")
    return goals


def goal_number(goal_file: Path) -> Optional[int]:
    match = re.match(r"G(\d{2})", goal_file.name)
    return int(match.group(1)) if match else None


def stage_for_goal_number(number: int) -> Optional[Tuple[str, int, int]]:
    for stage in STAGE_DEFINITIONS:
        _, start, end = stage
        if start <= number <= end:
            return stage
    return None


def stage_for_goal(goal_file: Path) -> Optional[Tuple[str, int, int]]:
    number = goal_number(goal_file)
    if number is None:
        return None
    return stage_for_goal_number(number)


def is_stage_boundary(goal_file: Path) -> bool:
    stage = stage_for_goal(goal_file)
    number = goal_number(goal_file)
    return stage is not None and number == stage[2]


def stage_lines() -> str:
    return "\n".join(
        f"- {name}: G{start:02d} through G{end:02d}"
        for name, start, end in STAGE_DEFINITIONS
    )


def goals_through_stage_boundary(goals: List[Path], boundary_goal: Path) -> List[Path]:
    boundary_number = goal_number(boundary_goal)
    if boundary_number is None:
        return [boundary_goal]
    return [
        goal
        for goal in goals
        if (number := goal_number(goal)) is not None and number <= boundary_number
    ]


def stage_ordinal_for_goal_index(goals: List[Path], index: int) -> Optional[int]:
    if index < 0 or index >= len(goals):
        return None
    number = goal_number(goals[index])
    if number is None:
        return None
    for ordinal, (_, start, end) in enumerate(STAGE_DEFINITIONS):
        if start <= number <= end:
            return ordinal
    return None


def extract_validation_commands(goal_text: str) -> str:
    """Extract fenced bash block(s) under '## Validation commands'."""
    lines = goal_text.splitlines()
    in_section = False
    in_fence = False
    commands: List[str] = []

    for line in lines:
        if line.startswith("## "):
            if in_section and not line.lower().startswith("## validation commands"):
                break
            in_section = line.lower().strip() == "## validation commands"
            continue

        if not in_section:
            continue

        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue

        if in_fence:
            commands.append(line)

    return "\n".join(commands).strip()


def initial_state(goals: List[Path], workspace: Path) -> Dict[str, Any]:
    return {
        "workspace": str(workspace),
        "created_at": dt.datetime.now().isoformat(),
        "updated_at": dt.datetime.now().isoformat(),
        "goals": [
            {
                "index": i,
                "file": str(g),
                "name": g.name,
                "status": STATUS_PENDING,
                "attempts": 0,
                "last_result": None,
                "last_verified_at": None,
            }
            for i, g in enumerate(goals)
        ],
    }


def reconcile_state(state: Dict[str, Any], goals: List[Path], workspace: Path) -> Dict[str, Any]:
    existing_by_name = {g["name"]: g for g in state.get("goals", [])}
    reconciled = initial_state(goals, workspace)
    for item in reconciled["goals"]:
        old = existing_by_name.get(item["name"])
        if old:
            item["status"] = old.get("status", STATUS_PENDING)
            item["attempts"] = old.get("attempts", 0)
            item["last_result"] = old.get("last_result")
            item["last_verified_at"] = old.get("last_verified_at")
    reconciled["created_at"] = state.get("created_at", reconciled["created_at"])
    reconciled["updated_at"] = dt.datetime.now().isoformat()
    return reconciled


def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = dt.datetime.now().isoformat()
    write_json(state_file, state)


def find_first_not_done(state: Dict[str, Any]) -> Optional[int]:
    for g in state["goals"]:
        if g.get("status") != STATUS_DONE:
            return int(g["index"])
    return None


def mark_from_pending(state: Dict[str, Any], start_idx: int) -> None:
    for g in state["goals"]:
        if int(g["index"]) >= start_idx:
            if g.get("status") == STATUS_DONE:
                g["status"] = STATUS_PENDING


def build_codex_base_cmd(args: argparse.Namespace, sandbox: str, output_file: Path) -> List[str]:
    # Put global flags before the subcommand for broad CLI-version compatibility.
    cmd = [
        args.codex_bin,
        "--ask-for-approval",
        args.approval,
    ]
    if args.model:
        cmd.extend(["--model", args.model])
    cmd.extend([
        "exec",
        "-C",
        str(args.workspace),
        "--sandbox",
        sandbox,
        "--output-schema",
        str(args.schema_file),
        "-o",
        str(output_file),
    ])
    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    cmd.append("-")
    return cmd


def build_validation_command(commands: str, validation_shell: str) -> List[str]:
    shell = validation_shell
    if shell == "auto":
        shell = "powershell" if is_windows() else "bash"

    if shell == "bash":
        return ["bash", "-lc", commands]
    if shell == "powershell":
        script = "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                commands,
                "if ($null -ne $global:LASTEXITCODE) { exit $global:LASTEXITCODE }",
            ]
        )
        return ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script]
    if shell == "cmd":
        return ["cmd", "/d", "/s", "/c", commands]
    raise ValueError(f"Unsupported validation shell: {validation_shell}")


def split_path_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [part.strip().strip('"') for part in raw.split(os.pathsep) if part.strip()]


def path_entry_for_tool(raw: str) -> str:
    path = Path(os.path.expandvars(raw.strip().strip('"')))
    if path.suffix.lower() in {".bat", ".cmd", ".com", ".exe"}:
        return str(path.parent)
    return str(path)


def discover_windows_validation_tools() -> Dict[str, str]:
    if not is_windows():
        return {}

    script = "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            "$pythonCommand = Get-Command python -ErrorAction SilentlyContinue",
            "$python = if ($pythonCommand) { $pythonCommand.Source } else { $null }",
            "$makeCommand = Get-Command make -ErrorAction SilentlyContinue",
            "$makeItem = if ($makeCommand) { Get-Item $makeCommand.Source } else { $null }",
            "$make = if ($makeItem -and $makeItem.Target) { $makeItem.Target[0] } elseif ($makeCommand) { $makeCommand.Source } else { $null }",
            "[pscustomobject]@{python=$python; make=$make} | ConvertTo-Json -Compress",
        ]
    )
    code, stdout, _ = run_command(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        cwd=Path.cwd(),
    )
    if code != 0 or not stdout.strip():
        return {}

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    return {key: str(value) for key, value in data.items() if value}


def build_validation_env(args: argparse.Namespace) -> Dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHON", None)
    prepended: List[str] = []

    for raw in split_path_list(os.environ.get("CODEX_GOAL_RUNNER_PATH_PREPEND")):
        prepended.append(path_entry_for_tool(raw))
    for raw_arg in getattr(args, "validation_path_prepend", []) or []:
        for raw in split_path_list(raw_arg):
            prepended.append(path_entry_for_tool(raw))

    python_bin = getattr(args, "validation_python", None) or os.environ.get("CODEX_GOAL_RUNNER_PYTHON")
    make_bin = getattr(args, "validation_make", None) or os.environ.get("CODEX_GOAL_RUNNER_MAKE")
    if (
        is_windows()
        and not getattr(args, "no_validation_tool_autodiscover", False)
        and (not python_bin or not make_bin)
    ):
        discovered = discover_windows_validation_tools()
        python_bin = python_bin or discovered.get("python")
        make_bin = make_bin or discovered.get("make")

    if python_bin:
        python_bin = python_bin.strip().strip('"')
        env["PYTHON"] = python_bin
        prepended.append(path_entry_for_tool(python_bin))

    if make_bin:
        make_bin = make_bin.strip().strip('"')
        prepended.append(path_entry_for_tool(make_bin))

    if prepended:
        existing_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(prepended + ([existing_path] if existing_path else []))
    return env


def goal_relative(path: Path, workspace: Path) -> str:
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


def parse_codex_result(result_path: Path) -> Dict[str, Any]:
    if not result_path.exists():
        return {
            "status": "fail",
            "goal_file": "",
            "earliest_failed_goal": None,
            "summary": f"Codex did not write result file: {result_path}",
            "changed_files": [],
            "validation": "missing result file",
            "blockers": ["missing result file"],
            "remaining_risks": [],
            "confidence": 0,
        }
    text = result_path.read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Sometimes tools may wrap JSON in markdown despite schema. Try to recover first object.
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {
            "status": "fail",
            "goal_file": "",
            "earliest_failed_goal": None,
            "summary": "Codex result was not valid JSON.",
            "changed_files": [],
            "validation": text[:2000],
            "blockers": ["invalid JSON result"],
            "remaining_risks": [],
            "confidence": 0,
        }


def validation_failure_result(goal_file: Path, workspace: Path, label: str, reason: str, log_path: Optional[Path]) -> Dict[str, Any]:
    current_rel = goal_relative(goal_file, workspace)
    validation = reason
    if log_path and log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = text[-4000:] if len(text) > 4000 else text
        validation = f"{reason}\n\nValidation log excerpt from {goal_relative(log_path, workspace)}:\n{excerpt}".strip()

    return {
        "status": "fail",
        "goal_file": current_rel,
        "earliest_failed_goal": current_rel,
        "summary": f"{label} validation failed for {current_rel}.",
        "changed_files": [],
        "validation": validation,
        "blockers": [reason],
        "remaining_risks": ["The failed validation must be fixed before this goal can be marked done."],
        "confidence": 1,
    }


def run_validation(goal_file: Path, args: argparse.Namespace, run_dir: Path, label: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    text = read_file(goal_file)
    commands = extract_validation_commands(text)
    if not commands:
        print_step(f"No validation commands found for {goal_file.name}; treating validation as failed.")
        log_path = run_dir / f"{label}.validation.missing.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "No validation commands found under ## Validation commands.\n", encoding="utf-8"
        )
        return False, validation_failure_result(
            goal_file,
            args.workspace,
            label,
            "No validation commands found under ## Validation commands.",
            log_path,
        )

    log_path = run_dir / f"{label}.validation.log"
    cmd = build_validation_command(commands, args.validation_shell)
    print_step(f"Running validation for {goal_file.name} with {cmd[0]}: {commands!r}")
    code, _, _ = run_command(cmd, cwd=args.workspace, log_path=log_path, env=build_validation_env(args))
    if code == 0:
        print_step(f"Validation passed for {goal_file.name}")
        return True, None
    print_step(f"Validation failed for {goal_file.name}; see {log_path}")
    return False, validation_failure_result(
        goal_file,
        args.workspace,
        label,
        f"Validation command failed with exit code {code}: {commands}",
        log_path,
    )


def run_stage_validation(
    stage_name: str,
    goal_files: List[Path],
    args: argparse.Namespace,
    run_dir: Path,
    label: str,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    commands_by_text: Dict[str, Path] = {}
    for goal_file in goal_files:
        commands = extract_validation_commands(read_file(goal_file))
        if not commands:
            log_path = run_dir / f"{label}.validation.missing.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                f"No validation commands found under ## Validation commands in {goal_file.name}.\n",
                encoding="utf-8",
            )
            return False, validation_failure_result(
                goal_file,
                args.workspace,
                f"{stage_name} stage",
                "No validation commands found under ## Validation commands.",
                log_path,
            )
        commands_by_text.setdefault(commands, goal_file)

    for ordinal, (commands, source_goal) in enumerate(commands_by_text.items(), start=1):
        log_path = run_dir / f"{label}.validation-{ordinal:02d}.log"
        cmd = build_validation_command(commands, args.validation_shell)
        print_step(
            f"Running {stage_name} stage validation with {cmd[0]} "
            f"from {source_goal.name}: {commands!r}"
        )
        code, _, _ = run_command(cmd, cwd=args.workspace, log_path=log_path, env=build_validation_env(args))
        if code != 0:
            print_step(f"{stage_name} stage validation failed; see {log_path}")
            return False, validation_failure_result(
                source_goal,
                args.workspace,
                f"{stage_name} stage",
                f"Validation command failed with exit code {code}: {commands}",
                log_path,
            )

    print_step(f"{stage_name} stage validation passed")
    return True, None


def format_retry_context(result: Optional[Dict[str, Any]]) -> str:
    if not result or result.get("status") == "pass":
        return "- none"

    lines = [
        f"- status: {result.get('status', 'unknown')}",
        f"- earliest_failed_goal: {result.get('earliest_failed_goal')}",
    ]
    if result.get("_requires_concrete_repair"):
        repair_gate = result.get("_repair_gate") or result.get("_regressed_from_stage") or "a stage gate"
        repair_failed_goal = result.get("_repair_failed_goal") or result.get("earliest_failed_goal")
        lines.append(
            f"- requires_concrete_repair: true; {repair_gate} rolled back to {repair_failed_goal}; "
            "returning pass requires actual git-detected changes in implementation, tests, specs, "
            "scripts, database schema, or root goal documents"
        )
    summary = str(result.get("summary", "")).strip()
    if summary:
        lines.append(f"- summary: {summary}")
    blockers = result.get("blockers") or []
    if blockers:
        lines.append("- blockers:")
        lines.extend(f"  - {blocker}" for blocker in blockers)
    validation = str(result.get("validation", "")).strip()
    if validation:
        lines.append(f"- validation: {validation}")
    remaining_risks = result.get("remaining_risks") or []
    if remaining_risks:
        lines.append("- remaining_risks:")
        lines.extend(f"  - {risk}" for risk in remaining_risks)
    return "\n".join(lines)


def build_execute_prompt(
    goal_file: Path,
    goals: List[Path],
    index: int,
    workspace: Path,
    retry_result: Optional[Dict[str, Any]] = None,
) -> str:
    previous = "\n".join(f"- {goal_relative(p, workspace)}" for p in goals[:index]) or "- none"
    current_rel = goal_relative(goal_file, workspace)
    all_goal_order = "\n".join(f"{i:02d}. {goal_relative(p, workspace)}" for i, p in enumerate(goals))
    retry_context = format_retry_context(retry_result)
    current_stage = stage_for_goal(goal_file)
    current_stage_line = (
        f"{current_stage[0]} (G{current_stage[1]:02d} through G{current_stage[2]:02d})"
        if current_stage
        else "- unknown"
    )

    return f"""
You are running a STRICT SEQUENTIAL GOAL PIPELINE.

Goal order:
{all_goal_order}

Stage gates:
{stage_lines()}

Current goal index: {index:02d}
Current goal file: {current_rel}
Current stage: {current_stage_line}
Previous goal files that must remain fully satisfied:
{previous}

Current retry context from the most recent failed verifier or execution:
{retry_context}

Hard rules:
1. Execute exactly the current goal file: {current_rel}.
2. Do NOT execute any later goal file.
3. Treat every previous goal as a regression contract. Do not break previous goals.
4. Before implementing, read the current goal file and all previous goal files.
5. If you discover that an earlier goal is not fully satisfied, stop current work and return status "fail" with earliest_failed_goal set to that earlier Gxx file. Do not start later work.
6. Implement only what is needed for the current goal's Objective, Required deliverables, Acceptance criteria, Constraints, and Non-goals.
7. Outer validation gates run only at stage boundaries G02, G07, G10, and G12. For non-boundary goals, run focused checks if feasible and expect the outer runner to defer full validation until the stage boundary.
8. Never weaken policy boundaries. Never copy legacy implementation code. Never merge Development Codex and Service Codex Runner realms.
9. Do not install new dependencies, perform destructive changes, deploy, access production data, or apply DDL/DML unless the current goal explicitly permits it.
10. Finish with JSON only, matching the provided schema.
11. If retry context is not "- none", address those blockers explicitly before returning "pass"; if a blocker is not valid, explain why in summary and validation.
12. Regression repair may include implementation, tests, specs, and root development goal documents up to and including {current_rel}. You may strengthen the current goal file or previous goal files when the retry context exposes missing acceptance criteria, missing validation commands, vague deliverables, or missing regression coverage.
13. Do not edit later goal files. Do not weaken or delete any Objective, Non-goal, Constraint, Acceptance criterion, Validation command, Stop condition, safety policy, or realm boundary. Goal-document changes must make the contract stricter, clearer, or more verifiable.
14. If retry context says requires_concrete_repair because a stage gate rolled back to this goal, "pass" requires changed_files to name at least one implementation, test, spec, script, database-schema, or goal-document contract change that directly repairs or captures that rollback. The outer runner will reject self-reported changed_files unless git detects matching concrete repository changes from this execution.

Definition of pass:
- The current goal's acceptance criteria are satisfied.
- If this is a stage-boundary goal, the completed stage's validation commands pass, or you clearly explain what command the outer runner must run. If this is not a stage-boundary goal, full validation may be deferred to the stage boundary.
- All previous goals still appear satisfied.
- No stop condition, non-goal, or constraint is violated.
- If retry context identified a real gap, changed_files must include at least one implementation, test, spec, or goal-document change that directly closes or captures that gap.
""".strip()


def build_verify_prompt(goal_file: Path, goals: List[Path], index: int, workspace: Path) -> str:
    current_rel = goal_relative(goal_file, workspace)
    previous = "\n".join(f"- {goal_relative(p, workspace)}" for p in goals[:index]) or "- none"

    return f"""
You are a STRICT READ-ONLY VERIFIER for a sequential Codex goal pipeline.

Verify this goal only: {current_rel}
Goal index: {index:02d}
Previous goals that must also remain compatible:
{previous}

Hard rules:
1. Do not modify files.
2. Read the goal file and inspect the repository state.
3. Check Objective, Required deliverables, Acceptance criteria, Constraints, Non-goals, and Stop conditions.
4. Return status "pass" only if the goal is fully satisfied and no previous-goal contract appears broken.
5. If any earlier goal is now not satisfied, return status "fail" and set earliest_failed_goal to that earlier Gxx file.
6. If this goal is incomplete, return status "fail" and set earliest_failed_goal to {current_rel}.
7. If blocked by missing context or ambiguous requirements, return status "blocked".
8. When returning "fail" or "blocked", make blockers actionable: identify the concrete implementation, test, spec, or goal-document gap that should be repaired. If the goal document is too vague to verify the intended contract, say that explicitly.
9. Finish with JSON only, matching the provided schema.

Important: The outer runner separately runs the goal's Validation commands. Your job is semantic acceptance verification.
""".strip()


def build_stage_verify_prompt(
    stage_name: str,
    boundary_goal: Path,
    included_goals: List[Path],
    workspace: Path,
) -> str:
    boundary_rel = goal_relative(boundary_goal, workspace)
    included = "\n".join(f"- {goal_relative(p, workspace)}" for p in included_goals)

    return f"""
You are a STRICT READ-ONLY VERIFIER for a sequential Codex stage gate.

Stage gate: {stage_name}
Stage boundary goal: {boundary_rel}

Stage definitions:
{stage_lines()}

Goal files included in this stage validation:
{included}

Hard rules:
1. Do not modify files.
2. Read every included goal file and inspect the repository state.
3. Check Objective, Required deliverables, Acceptance criteria, Constraints, Non-goals, and Stop conditions for every included goal.
4. Return status "pass" only if every included goal is fully satisfied and no prior-stage contract appears broken.
5. If any included goal is now not satisfied, return status "fail" and set earliest_failed_goal to the earliest failing Gxx file.
6. If blocked by missing context or ambiguous requirements, return status "blocked".
7. When returning "fail" or "blocked", make blockers actionable: identify the concrete implementation, test, spec, or goal-document gap that should be repaired. If the goal document is too vague to verify the intended contract, say that explicitly.
8. Finish with JSON only, matching the provided schema.

Important: The outer runner separately runs the stage's deduplicated Validation commands. Your job is semantic stage acceptance verification.
""".strip()


def run_codex_for_prompt(
    args: argparse.Namespace,
    prompt: str,
    run_dir: Path,
    label: str,
    sandbox: str,
) -> Dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / f"{label}.prompt.txt"
    output_path = run_dir / f"{label}.result.json"
    raw_log_path = run_dir / f"{label}.codex.log"
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    cmd = build_codex_base_cmd(args, sandbox=sandbox, output_file=output_path)
    print_step(f"Codex {label} started")
    code, _, _ = run_command(cmd, cwd=args.workspace, log_path=raw_log_path, input_text=prompt)
    result = parse_codex_result(output_path)
    result["_exit_code"] = code
    result["_result_path"] = str(output_path)
    result["_log_path"] = str(raw_log_path)
    if code != 0 and result.get("status") == "pass":
        result["status"] = "fail"
        result.setdefault("blockers", []).append(f"codex exec exited with {code}")
    return result


def verifier_passed(result: Dict[str, Any]) -> bool:
    return result.get("status") == "pass" and int(result.get("_exit_code", 1)) == 0


def earliest_failed_index(result: Dict[str, Any], goals: List[Path], default: int) -> int:
    raw = result.get("earliest_failed_goal")
    if not raw:
        return default
    raw_s = str(raw)
    for i, p in enumerate(goals):
        if p.name in raw_s or str(p) in raw_s or goal_relative(p, p.parent.parent if p.parent.name == "goals" else Path.cwd()) in raw_s:
            return i
    m = re.search(r"G(\d{2})", raw_s)
    if m:
        n = int(m.group(1))
        if 0 <= n < len(goals):
            return n
    return default


def annotate_stage_gate_repair_required(
    result: Dict[str, Any],
    goals: List[Path],
    boundary_idx: int,
    failed_idx: int,
    stage_name: str,
) -> Dict[str, Any]:
    if failed_idx <= boundary_idx:
        result["_requires_concrete_repair"] = True
        result["_repair_gate"] = stage_name
        result["_repair_boundary_goal"] = goals[boundary_idx].name
        result["_repair_failed_goal"] = goals[failed_idx].name

    boundary_stage = stage_ordinal_for_goal_index(goals, boundary_idx)
    failed_stage = stage_ordinal_for_goal_index(goals, failed_idx)
    if boundary_stage is not None and failed_stage is not None and failed_stage < boundary_stage:
        result["_regressed_from_stage"] = stage_name
    return result


def annotate_previous_stage_regression(
    result: Dict[str, Any],
    goals: List[Path],
    boundary_idx: int,
    failed_idx: int,
    stage_name: str,
) -> Dict[str, Any]:
    return annotate_stage_gate_repair_required(result, goals, boundary_idx, failed_idx, stage_name)


def result_has_concrete_changed_files(result: Dict[str, Any]) -> bool:
    return any(str(path).strip() for path in result.get("changed_files") or [])


def concrete_repair_failure_result(
    goal_file: Path,
    workspace: Path,
    retry_result: Dict[str, Any],
    reason: Optional[str] = None,
    actual_changed_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    current_rel = goal_relative(goal_file, workspace)
    regression_stage = retry_result.get("_repair_gate") or retry_result.get("_regressed_from_stage", "a later stage gate")
    reason = reason or (
        "Stage-gate rollback repair requires changed_files to include at least one "
        "implementation, test, spec, script, database-schema, or goal-document contract change "
        "that git confirms was changed during this execution."
    )
    observed = actual_changed_files or []
    validation = reason
    if observed:
        validation = f"{reason}\n\nGit-observed concrete changes: {', '.join(observed)}"
    return {
        "status": "fail",
        "goal_file": current_rel,
        "earliest_failed_goal": current_rel,
        "summary": f"Concrete repair evidence is missing after rollback from {regression_stage}.",
        "changed_files": [],
        "validation": validation,
        "blockers": [reason],
        "remaining_risks": ["The regression cannot be marked complete without concrete changed_files evidence."],
        "confidence": 1,
        "_requires_concrete_repair": True,
        "_repair_gate": regression_stage,
        "_actual_changed_files": observed,
    }


def relative_pathspec(path: Path, workspace: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix().rstrip("/")
    except ValueError:
        return None


def normalize_repo_path(path: str, workspace: Optional[Path] = None) -> str:
    raw = str(path).strip().strip('"')
    if workspace:
        candidate = Path(raw)
        if candidate.is_absolute():
            try:
                raw = candidate.resolve().relative_to(workspace.resolve()).as_posix()
            except (OSError, ValueError):
                pass
    raw = raw.replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    return raw.rstrip("/")


def is_generated_change_path(path: str, state_rel: Optional[str] = None) -> bool:
    normalized = normalize_repo_path(path)
    if not normalized:
        return True
    if state_rel and (normalized == state_rel or normalized.startswith(f"{state_rel}/")):
        return True
    if normalized.endswith(".pyc") or normalized.endswith(".pyo"):
        return True
    if "/__pycache__/" in f"/{normalized}/":
        return True
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in GENERATED_CHANGE_PREFIXES)


def is_concrete_repair_path(path: str) -> bool:
    normalized = normalize_repo_path(path)
    if is_generated_change_path(normalized):
        return False
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in CONCRETE_REPAIR_PREFIXES)


def parse_git_status_paths(raw: str) -> List[str]:
    paths: List[str] = []
    parts = raw.split("\0")
    idx = 0
    while idx < len(parts):
        entry = parts[idx]
        if not entry:
            idx += 1
            continue
        if len(entry) < 4:
            idx += 1
            continue
        status = entry[:2]
        paths.append(normalize_repo_path(entry[3:]))
        if "R" in status or "C" in status:
            idx += 1
            if idx < len(parts) and parts[idx]:
                paths.append(normalize_repo_path(parts[idx]))
        idx += 1
    return paths


def file_fingerprint(workspace: Path, rel_path: str) -> str:
    path = workspace / Path(rel_path)
    try:
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(chunk)
            return f"file:{digest.hexdigest()}"
        if path.exists():
            stat = path.stat()
            return f"other:{stat.st_mtime_ns}:{stat.st_size}"
        return "missing"
    except OSError as exc:
        return f"error:{type(exc).__name__}:{exc}"


def git_worktree_snapshot(workspace: Path, state_dir: Path) -> Dict[str, Any]:
    code, stdout, stderr = run_command(
        build_git_command(workspace, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]),
        cwd=workspace,
    )
    if code != 0:
        detail = (stderr or stdout or "git status failed").strip()
        return {"ok": False, "error": detail, "files": {}}

    state_rel = relative_pathspec(state_dir, workspace)
    files: Dict[str, str] = {}
    for path in parse_git_status_paths(stdout):
        normalized = normalize_repo_path(path)
        if is_generated_change_path(normalized, state_rel):
            continue
        files[normalized] = file_fingerprint(workspace, normalized)
    return {"ok": True, "error": "", "files": files}


def concrete_repair_changes_since_snapshot(
    before: Dict[str, Any],
    after: Dict[str, Any],
) -> Tuple[Optional[List[str]], Optional[str]]:
    if not before.get("ok"):
        return None, f"Cannot verify concrete repair changes before execution: {before.get('error')}"
    if not after.get("ok"):
        return None, f"Cannot verify concrete repair changes after execution: {after.get('error')}"

    before_files = before.get("files") or {}
    after_files = after.get("files") or {}
    changed = sorted(
        path
        for path in set(before_files) | set(after_files)
        if before_files.get(path) != after_files.get(path) and is_concrete_repair_path(path)
    )
    return changed, None


def normalized_changed_files(paths: List[str], workspace: Path) -> List[str]:
    return [normalize_repo_path(path, workspace) for path in paths if str(path).strip()]


def validate_concrete_repair_evidence(
    result: Dict[str, Any],
    actual_changed_files: List[str],
    workspace: Path,
) -> Tuple[bool, str]:
    actual = set(normalized_changed_files(actual_changed_files, workspace))
    reported = set(normalized_changed_files(result.get("changed_files") or [], workspace))
    reported_concrete = {path for path in reported if is_concrete_repair_path(path)}

    if not actual:
        return False, (
            "Stage-gate rollback repair requires actual git-detected changes in implementation, "
            "tests, specs, scripts, database schema, or root goal documents; none were detected."
        )
    if not reported_concrete:
        return False, (
            "Stage-gate rollback repair requires the Codex result changed_files to name a concrete "
            "implementation, test, spec, script, database-schema, or goal-document file."
        )
    if not (reported_concrete & actual):
        return False, (
            "Codex result changed_files did not match the concrete files git detected for this execution. "
            f"reported={sorted(reported_concrete)} actual={sorted(actual)}"
        )
    return True, ""


def build_git_add_command(args: argparse.Namespace) -> List[str]:
    cmd = build_git_command(args.workspace, ["add", "-A", "--", "."])
    state_rel = relative_pathspec(args.state_dir, args.workspace)
    if state_rel:
        cmd.append(f":(exclude){state_rel}/")
    return cmd


def auto_commit_if_requested(args: argparse.Namespace, goal_file: Path, run_dir: Path) -> None:
    if not args.auto_commit:
        return
    message = f"codex-goal: complete {goal_file.stem}"
    print_step(f"Auto-committing checkpoint: {message}")
    run_command(build_git_add_command(args), cwd=args.workspace, log_path=run_dir / "git-add.log")
    code, _, _ = run_command(
        build_git_command(args.workspace, ["commit", "-m", message]),
        cwd=args.workspace,
        log_path=run_dir / "git-commit.log",
    )
    if code != 0:
        print_step("Auto-commit skipped or failed; see git-commit.log")


def acquire_lock(lock_path: Path) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\ncreated_at={dt.datetime.now().isoformat()}\n")
    except FileExistsError:
        raise SystemExit(f"Runner lock exists: {lock_path}. Remove it only if no runner is active.")


def release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def status_summary(state: Dict[str, Any]) -> str:
    return ", ".join(f"{g['name']}={g['status']}" for g in state["goals"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict sequential Codex goal runner")
    parser.add_argument("--workspace", default=".", type=Path, help="Workspace/repo root")
    parser.add_argument("--goals-dir", default="goals", type=Path, help="Directory containing G*.md goal files")
    parser.add_argument("--state-dir", default=".codex-goals", type=Path, help="State/log directory")
    parser.add_argument("--model", default=None, help="Optional Codex model override")
    parser.add_argument("--codex-bin", default=None, help="Codex CLI executable; Windows auto-detects codex.cmd")
    parser.add_argument("--approval", default="never", choices=["untrusted", "on-request", "never"], help="Codex approval mode")
    parser.add_argument("--sandbox", default="workspace-write", choices=["read-only", "workspace-write", "danger-full-access"], help="Sandbox for execution runs")
    parser.add_argument("--verify-sandbox", default="read-only", choices=["read-only", "workspace-write", "danger-full-access"], help="Sandbox for semantic verification runs")
    parser.add_argument("--validation-shell", default="auto", choices=["auto", "bash", "powershell", "cmd"], help="Shell used for goal validation commands")
    parser.add_argument("--validation-path-prepend", action="append", default=[], help="Extra PATH entries for validation commands; repeatable and may contain OS path separators")
    parser.add_argument("--validation-python", default=None, help="Python executable used by Makefile validation through the PYTHON environment variable")
    parser.add_argument("--validation-make", default=None, help="Make executable path; its parent directory is prepended to validation PATH")
    parser.add_argument("--no-validation-tool-autodiscover", action="store_true", help="Disable Windows Get-Command autodiscovery for validation Python and Make")
    parser.add_argument("--max-rounds", type=int, default=80, help="Overall loop limit")
    parser.add_argument("--max-attempts-per-goal", type=int, default=5, help="Stop after this many execution attempts per goal")
    parser.add_argument("--skip-git-repo-check", action="store_true", help="Pass --skip-git-repo-check to Codex and bypass local git check")
    parser.add_argument("--auto-commit", action="store_true", help="Create a git commit after each verified goal")
    parser.add_argument("--no-semantic-verify", action="store_true", help="Only run validation commands; skip Codex read-only semantic verifier")
    parser.add_argument("--reset-state", action="store_true", help="Delete existing state and start from G00")
    parser.add_argument("--status", action="store_true", help="Print state and exit")
    args = parser.parse_args()

    args.workspace = args.workspace.resolve()
    args.goals_dir = (args.workspace / args.goals_dir).resolve() if not args.goals_dir.is_absolute() else args.goals_dir.resolve()
    args.state_dir = (args.workspace / args.state_dir).resolve() if not args.state_dir.is_absolute() else args.state_dir.resolve()
    args.schema_file = args.state_dir / "codex-goal-result.schema.json"

    args.codex_bin = ensure_codex(args.codex_bin)
    ensure_git_repo(args.workspace, args.skip_git_repo_check)

    goals = discover_goals(args.goals_dir)
    state_file = args.state_dir / "state.json"
    lock_file = args.state_dir / "runner.lock"
    write_json(args.schema_file, RESULT_SCHEMA)

    if args.reset_state and state_file.exists():
        state_file.unlink()

    state = reconcile_state(load_json(state_file, initial_state(goals, args.workspace)), goals, args.workspace)
    save_state(state_file, state)

    if args.status:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    acquire_lock(lock_file)
    try:
        rounds = 0
        while rounds < args.max_rounds:
            rounds += 1
            first_pending = find_first_not_done(state)
            if first_pending is None:
                print_step("All goals are complete and verified.")
                save_state(state_file, state)
                return 0

            print_step(f"Round {rounds}; next candidate: {state['goals'][first_pending]['name']}")

            current = state["goals"][first_pending]
            if current.get("attempts", 0) >= args.max_attempts_per_goal:
                print_step(f"Max attempts reached for {current['name']}; stopping.")
                current["status"] = STATUS_BLOCKED
                save_state(state_file, state)
                return 2

            goal_file = goals[first_pending]
            current["attempts"] = int(current.get("attempts", 0)) + 1
            current["status"] = STATUS_PENDING
            save_state(state_file, state)

            run_id = f"round-{rounds:03d}-execute-G{first_pending:02d}-attempt-{current['attempts']}-{now_stamp()}"
            run_dir = args.state_dir / "runs" / run_id
            retry_result = current.get("last_result")
            requires_concrete_repair = bool(retry_result and retry_result.get("_requires_concrete_repair"))
            repair_snapshot_before = (
                git_worktree_snapshot(args.workspace, args.state_dir)
                if requires_concrete_repair
                else None
            )
            prompt = build_execute_prompt(goal_file, goals, first_pending, args.workspace, retry_result)
            result = run_codex_for_prompt(args, prompt, run_dir, f"execute-G{first_pending:02d}", sandbox=args.sandbox)
            if requires_concrete_repair and verifier_passed(result):
                repair_snapshot_after = git_worktree_snapshot(args.workspace, args.state_dir)
                actual_changed_files, snapshot_error = concrete_repair_changes_since_snapshot(
                    repair_snapshot_before or {},
                    repair_snapshot_after,
                )
                if snapshot_error:
                    result = concrete_repair_failure_result(
                        goal_file,
                        args.workspace,
                        retry_result or {},
                        reason=snapshot_error,
                    )
                else:
                    result["_actual_changed_files"] = actual_changed_files or []
                    evidence_ok, evidence_error = validate_concrete_repair_evidence(
                        result,
                        actual_changed_files or [],
                        args.workspace,
                    )
                    if not evidence_ok:
                        result = concrete_repair_failure_result(
                            goal_file,
                            args.workspace,
                            retry_result or {},
                            reason=evidence_error,
                            actual_changed_files=actual_changed_files or [],
                        )
            current["last_result"] = result
            save_state(state_file, state)

            if not verifier_passed(result):
                failed_idx = earliest_failed_index(result, goals, first_pending)
                print_step(f"Codex execution did not pass. Returning to {state['goals'][failed_idx]['name']}.")
                mark_from_pending(state, failed_idx)
                state["goals"][failed_idx]["status"] = STATUS_FAILED
                state["goals"][failed_idx]["last_result"] = result
                save_state(state_file, state)
                continue

            if is_stage_boundary(goal_file):
                stage = stage_for_goal(goal_file)
                assert stage is not None
                stage_name, _, _ = stage
                stage_goals = goals_through_stage_boundary(goals, goal_file)
                validation_ok, validation_failure = run_stage_validation(
                    stage_name,
                    stage_goals,
                    args,
                    run_dir,
                    f"poststage-G{first_pending:02d}",
                )
                if not validation_ok:
                    failed_idx = earliest_failed_index(validation_failure or {}, goals, first_pending)
                    validation_failure = annotate_stage_gate_repair_required(
                        validation_failure or {},
                        goals,
                        first_pending,
                        failed_idx,
                        stage_name,
                    )
                    print_step(
                        f"{stage_name} stage validation failed; returning to {state['goals'][failed_idx]['name']}."
                    )
                    mark_from_pending(state, failed_idx)
                    state["goals"][failed_idx]["status"] = STATUS_FAILED
                    state["goals"][failed_idx]["last_result"] = validation_failure
                    save_state(state_file, state)
                    continue

                if not args.no_semantic_verify:
                    verify_prompt = build_stage_verify_prompt(stage_name, goal_file, stage_goals, args.workspace)
                    verify_result = run_codex_for_prompt(
                        args,
                        verify_prompt,
                        run_dir,
                        f"poststage-verify-G{first_pending:02d}",
                        sandbox=args.verify_sandbox,
                    )
                    current["last_result"] = verify_result
                    if not verifier_passed(verify_result):
                        failed_idx = earliest_failed_index(verify_result, goals, first_pending)
                        verify_result = annotate_stage_gate_repair_required(
                            verify_result,
                            goals,
                            first_pending,
                            failed_idx,
                            stage_name,
                        )
                        print_step(
                            f"{stage_name} semantic verification failed. Returning to {state['goals'][failed_idx]['name']}."
                        )
                        mark_from_pending(state, failed_idx)
                        state["goals"][failed_idx]["status"] = STATUS_FAILED
                        state["goals"][failed_idx]["last_result"] = verify_result
                        save_state(state_file, state)
                        continue

                verified_at = dt.datetime.now().isoformat()
                for j in range(first_pending + 1):
                    state["goals"][j]["last_verified_at"] = verified_at
                    if j < first_pending:
                        state["goals"][j]["status"] = STATUS_DONE
                save_state(state_file, state)
            else:
                stage = stage_for_goal(goal_file)
                if stage:
                    print_step(f"Stage validation deferred until {stage[0]} boundary G{stage[2]:02d}.")

            current["status"] = STATUS_DONE
            save_state(state_file, state)
            auto_commit_if_requested(args, goal_file, run_dir)
            print_step(f"Completed {current['name']}")
            print_step(f"State: {status_summary(state)}")

        print_step(f"Max rounds reached ({args.max_rounds}); stopping.")
        save_state(state_file, state)
        return 3
    finally:
        release_lock(lock_file)


if __name__ == "__main__":
    raise SystemExit(main())
