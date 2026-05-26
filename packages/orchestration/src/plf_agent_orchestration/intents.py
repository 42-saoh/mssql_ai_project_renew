from __future__ import annotations

import re

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

_METADATA_DOTTED_OBJECT_PATTERN = re.compile(
    r"\b(?:[a-z][a-z0-9_-]{0,63}\.){1,2}[a-z_][a-z0-9_$#@]{1,127}\b"
)
_METADATA_WORD_PATTERN = re.compile(r"\b[a-z][a-z0-9_$#@_-]{2,}\b")
_METADATA_GENERIC_TERMS = {
    "about",
    "all",
    "any",
    "column",
    "columns",
    "database",
    "databases",
    "db",
    "describe",
    "detail",
    "details",
    "find",
    "for",
    "from",
    "get",
    "information",
    "info",
    "list",
    "locate",
    "look",
    "lookup",
    "me",
    "metadata",
    "object",
    "objects",
    "please",
    "procedure",
    "procedures",
    "schema",
    "schemas",
    "search",
    "show",
    "sql",
    "table",
    "tables",
    "the",
    "up",
}
_KOREAN_WORD_PATTERN = re.compile(r"[가-힣][가-힣0-9_]*")
_KOREAN_CONTEXTUAL_TARGET_TERMS = {"이", "해당", "현재"}
_KOREAN_GENERIC_METADATA_TERMS = {
    "db",
    "객체",
    "검색",
    "검색해",
    "검색해줘",
    "데이터",
    "데이터베이스",
    "디비",
    "다",
    "들",
    "리스트",
    "메타데이터",
    "모든",
    "목록",
    "보여",
    "보여줘",
    "상세",
    "설명",
    "설명해",
    "설명해줘",
    "스키마",
    "알려",
    "알려줘",
    "아무",
    "저장",
    "전부",
    "전부다",
    "정보",
    "전체",
    "조회",
    "조회해",
    "조회해줘",
    "줘",
    "찾아",
    "찾아줘",
    "컬럼",
    "테이블",
    "프로시저",
    "일반",
    "해",
    "해줘",
}
_KOREAN_GENERIC_METADATA_FRAGMENTS = (
    "데이터베이스",
    "메타데이터",
    "프로시저",
    "테이블",
    "스키마",
    "컬럼",
    "객체",
)
_KOREAN_PARTICLE_SUFFIXES = (
    "으로부터",
    "으로",
    "에서",
    "에게",
    "보다",
    "처럼",
    "까지",
    "부터",
    "에는",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "의",
    "에",
    "도",
    "만",
    "와",
    "과",
    "로",
)


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
    if not (has_lookup_action and has_metadata_object):
        return False
    return _has_concrete_metadata_lookup_target(text)


def _has_concrete_metadata_lookup_target(text: str) -> bool:
    if _METADATA_DOTTED_OBJECT_PATTERN.search(text):
        return True
    if any(
        word not in _METADATA_GENERIC_TERMS
        for word in _METADATA_WORD_PATTERN.findall(text)
    ):
        return True
    return _has_concrete_unicode_metadata_lookup_target(text)


def _has_concrete_unicode_metadata_lookup_target(text: str) -> bool:
    for word in _KOREAN_WORD_PATTERN.findall(text):
        normalized = _strip_korean_particle(word)
        if normalized in _KOREAN_CONTEXTUAL_TARGET_TERMS:
            return True
        if _is_concrete_korean_metadata_target(normalized):
            return True
    return False


def _strip_korean_particle(word: str) -> str:
    for suffix in _KOREAN_PARTICLE_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix):
            return word[: -len(suffix)]
    return word


def _is_concrete_korean_metadata_target(word: str) -> bool:
    if not word or word in _KOREAN_GENERIC_METADATA_TERMS:
        return False
    reduced = word
    for fragment in _KOREAN_GENERIC_METADATA_FRAGMENTS:
        reduced = reduced.replace(fragment, "")
    return bool(reduced and reduced not in _KOREAN_GENERIC_METADATA_TERMS)
