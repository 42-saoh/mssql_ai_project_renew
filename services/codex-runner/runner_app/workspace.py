from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4


def create_workspace(base_dir: str | Path, runtime_template: str | Path) -> Path:
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    workspace = base / f"codexrun_{uuid4().hex}"
    shutil.copytree(runtime_template, workspace)
    (workspace / "input").mkdir(exist_ok=True)
    (workspace / "outputs").mkdir(exist_ok=True)
    (workspace / "scratch").mkdir(exist_ok=True)
    return workspace


def cleanup_workspace(path: str | Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
