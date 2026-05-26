from __future__ import annotations

from plf_agent_contracts.enums import Intent

from .forbidden_operations import detect_forbidden_operation_blockers

BLOCKED_EXECUTION_KEYWORDS = [
    "실행",
    "적용",
    "apply",
    "execute",
    "run sql",
    "ddl 적용",
    "dml",
    "프로시저 실행",
    "sp 실행",
]

DEPENDENCY_ACTION_TERMS = [
    "show",
    "review",
    "analyze",
    "analyse",
    "find",
    "list",
    "tell",
    "알려",
    "보여",
    "분석",
]

DRAFT_ACTION_TERMS = [
    "generate",
    "draft",
    "create",
    "make",
    "write",
    "작성",
    "생성",
    "만들",
    "초안",
]

METADATA_ACTION_TERMS = [
    "find",
    "search",
    "lookup",
    "look up",
    "locate",
    "show",
    "list",
    "describe",
    "get",
    "찾아",
    "검색",
    "조회",
    "보여",
    "알려",
]

METADATA_OBJECT_TERMS = [
    "metadata",
    "메타데이터",
    "column",
    "컬럼",
    "table",
    "테이블",
    "schema",
    "object",
    "procedure",
    "프로시저",
]


def classify_intent(message: str) -> Intent:
    text = (message or "").lower()

    if detect_forbidden_operation_blockers(message):
        return Intent.BLOCKED_OR_APPROVAL_REQUIRED

    if any(keyword in text for keyword in BLOCKED_EXECUTION_KEYWORDS):
        return Intent.BLOCKED_OR_APPROVAL_REQUIRED

    if any(keyword in text for keyword in ["지난번", "이전", "히스토리", "결과 보여"]):
        return Intent.HISTORY_LOOKUP

    if any(keyword in text for keyword in ["history", "artifact"]) and any(
        action in text
        for action in [
            "show",
            "list",
            "get",
            "find",
            "lookup",
            "look up",
            "보여",
            "조회",
        ]
    ):
        return Intent.HISTORY_LOOKUP

    if any(
        keyword in text for keyword in ["dependency", "dependencies", "의존", "참조"]
    ) and any(action in text for action in DEPENDENCY_ACTION_TERMS):
        return Intent.DEPENDENCY_ANALYSIS

    if any(
        keyword in text for keyword in ["mybatis", "java", "mapper", "서비스"]
    ) and any(action in text for action in DRAFT_ACTION_TERMS):
        return Intent.DRAFT_GENERATION

    if "테이블 생성" in text or "create table" in text or "테이블 설계" in text:
        return Intent.TABLE_DESIGN

    if _looks_like_metadata_search(text):
        return Intent.METADATA_SEARCH

    if ("분석" in text or "analysis" in text or "analyze" in text) and (
        "sp" in text or "procedure" in text or "프로시저" in text or ".dbo." in text
    ):
        return Intent.SP_ANALYSIS

    return Intent.BLOCKED


def _looks_like_metadata_search(text: str) -> bool:
    has_lookup_action = any(action in text for action in METADATA_ACTION_TERMS)
    has_metadata_object = any(term in text for term in METADATA_OBJECT_TERMS)
    return has_lookup_action and has_metadata_object
