from __future__ import annotations

FORBIDDEN_SQL_PREVIEW_TERMS = [
    "ALTER ",
    "DELETE ",
    "DROP ",
    "EXEC ",
    "EXECUTE ",
    "INSERT ",
    "MERGE ",
    "TRUNCATE ",
    "UPDATE ",
]


def validate_table_design_preview(script: str, *, blocked_from_auto_apply: bool = True) -> tuple[bool, list[str]]:
    upper = (script or "").upper()
    blockers = [term.strip() for term in FORBIDDEN_SQL_PREVIEW_TERMS if term in upper]
    if "CREATE TABLE" not in upper:
        blockers.append("MISSING_CREATE_TABLE")
    if blocked_from_auto_apply is not True:
        blockers.append("AUTO_APPLY_NOT_BLOCKED")
    return not blockers, blockers
