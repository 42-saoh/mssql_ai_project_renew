from __future__ import annotations

FORBIDDEN_SQL_PREVIEW_TERMS = ["EXEC ", "EXECUTE ", "INSERT ", "UPDATE ", "DELETE ", "DROP "]


def validate_table_design_preview(script: str) -> tuple[bool, list[str]]:
    upper = (script or "").upper()
    blockers = [term.strip() for term in FORBIDDEN_SQL_PREVIEW_TERMS if term in upper]
    if "CREATE TABLE" not in upper:
        blockers.append("MISSING_CREATE_TABLE")
    return not blockers, blockers
