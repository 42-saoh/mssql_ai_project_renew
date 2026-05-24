from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for rel in [
    "packages/contracts/src",
    "packages/orchestration/src",
    "packages/validation/src",
    "services/codex-runner",
]:
    path = str(ROOT / rel)
    if path not in sys.path:
        sys.path.insert(0, path)
