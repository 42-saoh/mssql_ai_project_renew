from __future__ import annotations

import json
from typing import Iterable

SAFE_EVENT_KEYS = {"type", "status", "id", "event_id", "timestamp", "duration_ms", "exit_code"}


def parse_jsonl_events(lines: Iterable[str]) -> list[dict]:
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            events.append(_safe_event(event if isinstance(event, dict) else {"type": "unknown"}))
        except json.JSONDecodeError:
            events.append({"type": "unparsed"})
    return events


def summarize_event_stream(stdout: str = "", stderr: str = "") -> dict:
    events = parse_jsonl_events(stdout.splitlines())
    event_types = sorted({str(event.get("type") or "unknown") for event in events})
    return {
        "eventCount": len(events),
        "eventTypes": event_types,
        "unparsedCount": sum(1 for event in events if event.get("type") == "unparsed"),
        "stderrLineCount": len([line for line in stderr.splitlines() if line.strip()]),
    }


def _safe_event(event: dict) -> dict:
    safe = {key: event[key] for key in SAFE_EVENT_KEYS if key in event}
    safe.setdefault("type", "unknown")
    return safe
