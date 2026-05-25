from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ForbiddenOperationRule:
    code: str
    patterns: tuple[re.Pattern[str], ...]


_IDENTIFIER = r"(?:\[[^\]]+\]|[a-z_][\w$]*|\*)"
_DOTTED_OBJECT = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER}){{1,2}}"
_KO_STORED_PROCEDURE = "(?:\uc800\uc7a5\\s*)?\ud504\ub85c\uc2dc\uc800"
_KO_OBJECT_PARTICLE = "(?:\\s*(?:\uc744|\ub97c))?"
_KO_EXECUTE_OR_CALL = "(?:\uc2e4\ud589|\ud638\ucd9c)"


_RULES = (
    ForbiddenOperationRule(
        "ROW_DATA_ACCESS_BLOCKED",
        (
            re.compile(r"\b(?:row\s+data|actual\s+rows?|select\s+\*)\b", re.I),
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
            re.compile(r"\bfree\s+sql\s+(?:execution|execute|run)\b", re.I),
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
    "ROW_DATA_ACCESS_BLOCKED",
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
    return blockers


def has_hard_blocker(blockers: list[str]) -> bool:
    return any(blocker in _HARD_BLOCKED_CODES for blocker in blockers)
