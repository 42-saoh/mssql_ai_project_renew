from __future__ import annotations

import re
from typing import Iterable

_SQL_SELECT_STATEMENT = re.compile(r"\bselect\b.{1,500}?\bfrom\b", re.I | re.S)
_ROW_DATA_CONTAINER = re.compile(
    r'"(?:rows|records|resultSet|result_set|resultSets|result_sets|sampleRows|sample_rows|values)"\s*:\s*\[',
    re.I,
)
_KO_ROW_DATA = re.compile(
    "(?:\ud589\\s*\ub370\uc774\ud130|\uc2e4\uc81c\\s*\ud589|\ub808\ucf54\ub4dc|\uc0d8\ud50c\\s*\ub370\uc774\ud130|"
    "(?<!\uba54\ud0c0)\ub370\uc774\ud130(?:\\s*(?:\uc744|\ub97c))?\\s*(?:\uc870\ud68c|\ubcf4\uc5ec|\ucd9c\ub825|\uac00\uc838|\uc77d\uc5b4))",
    re.I,
)

_PATTERNS = {
    "RAW_PROMPT": re.compile(r"raw[_ -]?prompt", re.I),
    "RAW_PROVIDER_RESPONSE": re.compile(r"raw[_ -]?provider|provider[_ -]?response", re.I),
    "ROW_DATA": re.compile(
        r"\b(row data|actual rows?|actual records?|sample data|table data|select \* from)\b",
        re.I,
    ),
    "SECRET": re.compile(r'\b"?(password|secret|api[_-]?key|token)"?\s*[:=]', re.I),
    "RAW_SP": re.compile(r"\bcreate\s+(or\s+alter\s+)?proc(edure)?\b", re.I),
}


def find_redaction_violations(text: str) -> list[str]:
    rendered = text or ""
    violations = [code for code, pattern in _PATTERNS.items() if pattern.search(rendered)]
    if (
        "ROW_DATA" not in violations
        and (
            _SQL_SELECT_STATEMENT.search(rendered)
            or _ROW_DATA_CONTAINER.search(rendered)
            or _KO_ROW_DATA.search(rendered)
        )
    ):
        violations.append("ROW_DATA")
    return violations


def contains_any_violation(parts: Iterable[str]) -> list[str]:
    found: list[str] = []
    for part in parts:
        for code in find_redaction_violations(part):
            if code not in found:
                found.append(code)
    return found
