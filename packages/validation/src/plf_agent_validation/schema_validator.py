from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_required_keys(obj: dict[str, Any], required: list[str]) -> tuple[bool, list[str]]:
    missing = [key for key in required if key not in obj]
    return not missing, missing
