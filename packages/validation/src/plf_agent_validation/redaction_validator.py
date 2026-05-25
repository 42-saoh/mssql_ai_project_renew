from __future__ import annotations

import re
from typing import Iterable

_PATTERNS = {
    "RAW_PROMPT": re.compile(r"raw[_ -]?prompt", re.I),
    "RAW_PROVIDER_RESPONSE": re.compile(r"raw[_ -]?provider|provider[_ -]?response", re.I),
    "ROW_DATA": re.compile(r"\b(row data|select \* from|actual rows)\b", re.I),
    "SECRET": re.compile(r'\b"?(password|secret|api[_-]?key|token)"?\s*[:=]', re.I),
    "RAW_SP": re.compile(r"\bcreate\s+(or\s+alter\s+)?proc(edure)?\b", re.I),
}


def find_redaction_violations(text: str) -> list[str]:
    return [code for code, pattern in _PATTERNS.items() if pattern.search(text or "")]


def contains_any_violation(parts: Iterable[str]) -> list[str]:
    found: list[str] = []
    for part in parts:
        for code in find_redaction_violations(part):
            if code not in found:
                found.append(code)
    return found
