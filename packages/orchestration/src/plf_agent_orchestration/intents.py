from __future__ import annotations

from plf_agent_contracts.enums import Intent

from .forbidden_operations import detect_forbidden_operation_blockers

BLOCKED_EXECUTION_KEYWORDS = [
    "실행", "적용", "apply", "execute", "run sql", "ddl 적용", "dml", "프로시저 실행", "sp 실행",
]

DB_DOMAIN_KEYWORDS = [
    "db", "database", "테이블", "컬럼", "column", "table", "sp", "procedure", "프로시저",
    "dependency", "의존", "mybatis", "java", "mapper", "metadata", "메타데이터", "쿼리", "sql",
]


def classify_intent(message: str) -> Intent:
    text = (message or "").lower()

    if detect_forbidden_operation_blockers(message):
        return Intent.BLOCKED_OR_APPROVAL_REQUIRED

    if any(keyword in text for keyword in BLOCKED_EXECUTION_KEYWORDS):
        return Intent.BLOCKED_OR_APPROVAL_REQUIRED

    if any(keyword in text for keyword in ["지난번", "이전", "히스토리", "history", "결과 보여", "artifact"]):
        return Intent.HISTORY_LOOKUP

    if "dependency" in text or "의존" in text or "참조" in text:
        return Intent.DEPENDENCY_ANALYSIS

    if "mybatis" in text or "java" in text or "mapper" in text or "초안" in text and "서비스" in text:
        return Intent.DRAFT_GENERATION

    if "테이블 생성" in text or "create table" in text or "테이블 설계" in text:
        return Intent.TABLE_DESIGN

    if "컬럼" in text or "column" in text or "테이블 찾아" in text or "metadata" in text or "메타데이터" in text:
        return Intent.METADATA_SEARCH

    if (
        ("분석" in text or "analysis" in text or "analyze" in text)
        and ("sp" in text or "procedure" in text or "프로시저" in text or ".dbo." in text)
    ):
        return Intent.SP_ANALYSIS

    if any(keyword in text for keyword in DB_DOMAIN_KEYWORDS):
        return Intent.METADATA_SEARCH

    return Intent.BLOCKED
