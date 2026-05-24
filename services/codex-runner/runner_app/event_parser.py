from __future__ import annotations

import json
from typing import Iterable


def parse_jsonl_events(lines: Iterable[str]) -> list[dict]:
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"type": "unparsed", "text": line})
    return events
