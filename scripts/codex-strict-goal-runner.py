#!/usr/bin/env python3
"""
Strict sequential Codex goal runner.

What it enforces:
1. Goal files are executed in lexical order: goals/G00..., G01..., G02...
2. Only one goal is given to Codex per run.
3. Before moving to a later goal, all previous goals are re-validated.
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


def run_command(
    cmd: List[str],
    cwd: Path,
    log_path: Optional[Path] = None,
    input_text: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as f:
            f.write("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n")
            if input_text:
                f.write("--- stdin ---\n")
                f.write(input_text)
                if not input_text.endswith("\n"):
                    f.write("\n")
                f.write("\n")
            f.write("--- stdout ---\n")
            f.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                f.write("\n")
            f.write("\n--- stderr ---\n")
            f.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                f.write("\n")
            f.write(f"\n--- exit_code ---\n{proc.returncode}\n")
    return proc.returncode, proc.stdout, proc.stderr


def ensure_codex() -> None:
    if shutil.which("codex") is None:
        raise SystemExit("codex CLI was not found on PATH. Install it first: npm i -g @openai/codex")


def ensure_git_repo(workspace: Path, skip: bool) -> None:
    if skip:
        return
    code, _, _ = run_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=workspace)
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
        "codex",
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


def run_validation(goal_file: Path, args: argparse.Namespace, run_dir: Path, label: str) -> bool:
    text = read_file(goal_file)
    commands = extract_validation_commands(text)
    if not commands:
        print_step(f"No validation commands found for {goal_file.name}; treating validation as failed.")
        (run_dir / f"{label}.validation.missing.log").write_text(
            "No validation commands found under ## Validation commands.\n", encoding="utf-8"
        )
        return False

    log_path = run_dir / f"{label}.validation.log"
    print_step(f"Running validation for {goal_file.name}: {commands!r}")
    code, _, _ = run_command(["bash", "-lc", commands], cwd=args.workspace, log_path=log_path)
    if code == 0:
        print_step(f"Validation passed for {goal_file.name}")
        return True
    print_step(f"Validation failed for {goal_file.name}; see {log_path}")
    return False


def build_execute_prompt(goal_file: Path, goals: List[Path], index: int, workspace: Path) -> str:
    previous = "\n".join(f"- {goal_relative(p, workspace)}" for p in goals[:index]) or "- none"
    current_rel = goal_relative(goal_file, workspace)
    all_goal_order = "\n".join(f"{i:02d}. {goal_relative(p, workspace)}" for i, p in enumerate(goals))

    return f"""
You are running a STRICT SEQUENTIAL GOAL PIPELINE.

Goal order:
{all_goal_order}

Current goal index: {index:02d}
Current goal file: {current_rel}
Previous goal files that must remain fully satisfied:
{previous}

Hard rules:
1. Execute exactly the current goal file: {current_rel}.
2. Do NOT execute any later goal file.
3. Treat every previous goal as a regression contract. Do not break previous goals.
4. Before implementing, read the current goal file and all previous goal files.
5. If you discover that an earlier goal is not fully satisfied, stop current work and return status "fail" with earliest_failed_goal set to that earlier Gxx file. Do not start later work.
6. Implement only what is needed for the current goal's Objective, Required deliverables, Acceptance criteria, Constraints, and Non-goals.
7. Run the current goal's Validation commands if feasible.
8. Never weaken policy boundaries. Never copy legacy implementation code. Never merge Development Codex and Service Codex Runner realms.
9. Do not install new dependencies, perform destructive changes, deploy, access production data, or apply DDL/DML unless the current goal explicitly permits it.
10. Finish with JSON only, matching the provided schema.

Definition of pass:
- The current goal's acceptance criteria are satisfied.
- The current goal's validation commands pass, or you clearly explain what command the outer runner must run.
- All previous goals still appear satisfied.
- No stop condition, non-goal, or constraint is violated.
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
8. Finish with JSON only, matching the provided schema.

Important: The outer runner separately runs the goal's Validation commands. Your job is semantic acceptance verification.
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


def auto_commit_if_requested(args: argparse.Namespace, goal_file: Path, run_dir: Path) -> None:
    if not args.auto_commit:
        return
    message = f"codex-goal: complete {goal_file.stem}"
    print_step(f"Auto-committing checkpoint: {message}")
    run_command(["git", "add", "-A"], cwd=args.workspace, log_path=run_dir / "git-add.log")
    code, _, _ = run_command(["git", "commit", "-m", message], cwd=args.workspace, log_path=run_dir / "git-commit.log")
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
    parser.add_argument("--approval", default="never", choices=["untrusted", "on-request", "never"], help="Codex approval mode")
    parser.add_argument("--sandbox", default="workspace-write", choices=["read-only", "workspace-write", "danger-full-access"], help="Sandbox for execution runs")
    parser.add_argument("--verify-sandbox", default="read-only", choices=["read-only", "workspace-write", "danger-full-access"], help="Sandbox for semantic verification runs")
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

    ensure_codex()
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

            # Re-verify every prior done goal before moving forward.
            regression_idx: Optional[int] = None
            for j in range(first_pending):
                goal_file = goals[j]
                run_id = f"round-{rounds:03d}-preverify-G{j:02d}-{now_stamp()}"
                run_dir = args.state_dir / "runs" / run_id

                if not run_validation(goal_file, args, run_dir, f"preverify-G{j:02d}"):
                    regression_idx = j
                    break

                if not args.no_semantic_verify:
                    prompt = build_verify_prompt(goal_file, goals, j, args.workspace)
                    result = run_codex_for_prompt(args, prompt, run_dir, f"preverify-G{j:02d}", sandbox=args.verify_sandbox)
                    state["goals"][j]["last_result"] = result
                    if not verifier_passed(result):
                        regression_idx = earliest_failed_index(result, goals, j)
                        break
                    state["goals"][j]["last_verified_at"] = dt.datetime.now().isoformat()
                    save_state(state_file, state)

            if regression_idx is not None:
                print_step(f"Regression detected at {state['goals'][regression_idx]['name']}; returning to that goal.")
                mark_from_pending(state, regression_idx)
                state["goals"][regression_idx]["status"] = STATUS_FAILED
                save_state(state_file, state)
                first_pending = regression_idx

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
            prompt = build_execute_prompt(goal_file, goals, first_pending, args.workspace)
            result = run_codex_for_prompt(args, prompt, run_dir, f"execute-G{first_pending:02d}", sandbox=args.sandbox)
            current["last_result"] = result
            save_state(state_file, state)

            if not verifier_passed(result):
                failed_idx = earliest_failed_index(result, goals, first_pending)
                print_step(f"Codex execution did not pass. Returning to {state['goals'][failed_idx]['name']}.")
                mark_from_pending(state, failed_idx)
                state["goals"][failed_idx]["status"] = STATUS_FAILED
                save_state(state_file, state)
                continue

            if not run_validation(goal_file, args, run_dir, f"postexecute-G{first_pending:02d}"):
                print_step(f"Post-execution validation failed for {current['name']}; retrying same goal later.")
                current["status"] = STATUS_FAILED
                save_state(state_file, state)
                continue

            if not args.no_semantic_verify:
                verify_prompt = build_verify_prompt(goal_file, goals, first_pending, args.workspace)
                verify_result = run_codex_for_prompt(args, verify_prompt, run_dir, f"postverify-G{first_pending:02d}", sandbox=args.verify_sandbox)
                current["last_result"] = verify_result
                if not verifier_passed(verify_result):
                    failed_idx = earliest_failed_index(verify_result, goals, first_pending)
                    print_step(f"Semantic verification failed. Returning to {state['goals'][failed_idx]['name']}.")
                    mark_from_pending(state, failed_idx)
                    state["goals"][failed_idx]["status"] = STATUS_FAILED
                    save_state(state_file, state)
                    continue

            current["status"] = STATUS_DONE
            current["last_verified_at"] = dt.datetime.now().isoformat()
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
