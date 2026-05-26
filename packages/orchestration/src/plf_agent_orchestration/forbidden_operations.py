from __future__ import annotations

import re
from dataclasses import dataclass

from plf_agent_validation.redaction_validator import find_redaction_violations


@dataclass(frozen=True)
class ForbiddenOperationRule:
    code: str
    patterns: tuple[re.Pattern[str], ...]


_IDENTIFIER = r"(?:\[[^\]]+\]|[a-z_][\w$]*|\*)"
_DOTTED_OBJECT = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER}){{1,2}}"
_SQL_SELECT_STATEMENT = (
    r"\bselect\s+(?:top\s*\(?\s*\d+\s*\)?\s+)?(?:distinct\s+)?"
    r".{1,500}?\s+from\s+"
    rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER}){{0,2}}\b"
)
_KO_STORED_PROCEDURE = "(?:\uc800\uc7a5\\s*)?\ud504\ub85c\uc2dc\uc800"
_KO_OBJECT_PARTICLE = "(?:\\s*(?:\uc744|\ub97c))?"
_KO_EXECUTE_OR_CALL = "(?:\uc2e4\ud589|\ud638\ucd9c)"
_KO_ROW_DATA = "\ud589\\s*\ub370\uc774\ud130"
_KO_ACTUAL_ROWS = "\uc2e4\uc81c\\s*\ud589"
_KO_RECORD = "\ub808\ucf54\ub4dc"
_KO_SAMPLE_DATA = "\uc0d8\ud50c\\s*\ub370\uc774\ud130"
_KO_DATA_ACTION = "(?:\uc870\ud68c|\ubcf4\uc5ec|\ucd9c\ub825|\uac00\uc838|\uc77d\uc5b4)"
_KO_SQL_OR_QUERY = "(?:sql|\ucffc\ub9ac)"
_KO_SQL_EXECUTION = "(?:\uc2e4\ud589|\uc218\ud589|\ub3cc\ub824|\uc870\ud68c)"


_RULES = (
    ForbiddenOperationRule(
        "ROW_DATA_ACCESS_BLOCKED",
        (
            re.compile(r"\b(?:row\s+data|actual\s+rows?|actual\s+records?|sample\s+data|table\s+data|select\s+\*)\b", re.I),
            re.compile(
                r"\b(?:show|display|list|return|get|fetch|view|export)\s+"
                r"(?:the\s+)?(?:\w+\s+){0,5}(?:rows?|records?|sample\s+data|table\s+data|data)\b",
                re.I,
            ),
            re.compile(r"\b(?:rows?|records?)\s+(?:from|in|for)\s+[\w\[\].]+", re.I),
            re.compile(f"(?:{_KO_ROW_DATA}|{_KO_ACTUAL_ROWS}|{_KO_RECORD}|{_KO_SAMPLE_DATA})", re.I),
            re.compile(f"(?<!\uba54\ud0c0)\ub370\uc774\ud130{_KO_OBJECT_PARTICLE}\\s*{_KO_DATA_ACTION}", re.I),
        ),
    ),
    ForbiddenOperationRule(
        "STORED_PROCEDURE_EXECUTION_BLOCKED",
        (
            re.compile(r"\b(?:run|call|exec|execute)\s+(?:the\s+)?(?:stored\s+)?(?:proc(?:edure)?|sp)\b", re.I),
            re.compile(rf"\b(?:run|call|exec|execute)\s+{_DOTTED_OBJECT}(?=$|[^\w])", re.I),
            re.compile(r"\b(?:stored\s+procedure|procedure|proc|sp)\s+(?:execution|execute|run|call)\b", re.I),
            re.compile(r"\bsp(?:\s|-|_)*(?:execution|execute|run|call)\b", re.I),
            re.compile(f"{_KO_STORED_PROCEDURE}{_KO_OBJECT_PARTICLE}\\s*{_KO_EXECUTE_OR_CALL}", re.I),
            re.compile(f"sp{_KO_OBJECT_PARTICLE}\\s*{_KO_EXECUTE_OR_CALL}", re.I),
        ),
    ),
    ForbiddenOperationRule(
        "FREE_SQL_EXECUTION_BLOCKED",
        (
            re.compile(r"\b(?:execute|run)\s+(?:this\s+)?sql\b", re.I),
            re.compile(r"\b(?:run|execute|submit|issue)\s+(?:this\s+)?(?:query|select)\b", re.I),
            re.compile(r"\bfree\s+sql\s+(?:execution|execute|run)\b", re.I),
            re.compile(_SQL_SELECT_STATEMENT, re.I | re.S),
            re.compile(f"\\b{_KO_SQL_OR_QUERY}\\s*{_KO_SQL_EXECUTION}", re.I),
        ),
    ),
    ForbiddenOperationRule(
        "DDL_DML_APPLY_BLOCKED",
        (
            re.compile(r"\b(?:apply|run|execute)\s+(?:this\s+)?(?:ddl|dml)\b", re.I),
            re.compile(r"\b(?:ddl|dml)\s+(?:apply|execution|run|execute)\b", re.I),
            re.compile("(?:ddl|dml)\\s*\uc801\uc6a9", re.I),
        ),
    ),
    ForbiddenOperationRule(
        "SOURCE_APPLY_OR_DEPLOY_BLOCKED",
        (
            re.compile(r"\b(?:apply|overwrite)\s+source\b", re.I),
            re.compile(r"\bdeploy\b", re.I),
            re.compile("\ubc30\ud3ec", re.I),
        ),
    ),
)

_HARD_BLOCKED_CODES = {
    "CONNECTION_STRING",
    "RAW_PROMPT",
    "RAW_PROVIDER_RESPONSE",
    "RAW_SP",
    "ROW_DATA_ACCESS_BLOCKED",
    "ROW_DATA",
    "SECRET",
    "STORED_PROCEDURE_EXECUTION_BLOCKED",
    "FREE_SQL_EXECUTION_BLOCKED",
    "SOURCE_APPLY_OR_DEPLOY_BLOCKED",
}


def detect_forbidden_operation_blockers(message: str) -> list[str]:
    text = message or ""
    blockers: list[str] = []
    for rule in _RULES:
        if any(pattern.search(text) for pattern in rule.patterns):
            blockers.append(rule.code)
    for code in find_redaction_violations(text):
        if code not in blockers:
            blockers.append(code)
    return blockers


def has_hard_blocker(blockers: list[str]) -> bool:
    return any(blocker in _HARD_BLOCKED_CODES for blocker in blockers)
