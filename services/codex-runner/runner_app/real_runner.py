from __future__ import annotations

import subprocess
from pathlib import Path

from .codex_exec import build_codex_exec_command


def run_real(workspace: str | Path) -> subprocess.CompletedProcess[str]:
    cmd = build_codex_exec_command(workspace)
    return subprocess.run(cmd, check=False, text=True, capture_output=True)
