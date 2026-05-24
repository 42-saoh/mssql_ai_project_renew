from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[2] / "codex-runner" / "runner_app" / "fake_runner.py"
_spec = importlib.util.spec_from_file_location("codex_runner_dash_fake_runner", _path)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)
run_fake = _mod.run_fake
