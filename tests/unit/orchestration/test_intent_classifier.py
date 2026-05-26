from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.intents import classify_intent


def test_supported_intents():
    assert classify_intent("PPM.dbo.X SP 분석해줘") == Intent.SP_ANALYSIS
    assert classify_intent("이 컬럼 찾아줘") == Intent.METADATA_SEARCH
    assert classify_intent("관련 dependency 알려줘") == Intent.DEPENDENCY_ANALYSIS
    assert classify_intent("주문 요청 테이블 생성 쿼리 초안 줘") == Intent.TABLE_DESIGN
    assert classify_intent("Java MyBatis 초안 만들어줘") == Intent.DRAFT_GENERATION
    assert classify_intent("지난번 결과 보여줘") == Intent.HISTORY_LOOKUP


def test_blocked_intents():
    assert classify_intent("이 DDL 적용해줘") == Intent.BLOCKED_OR_APPROVAL_REQUIRED
    assert classify_intent("오늘 점심 추천해줘") == Intent.BLOCKED


def test_db_themed_general_chat_is_not_metadata_search():
    assert classify_intent("What is SQL?") == Intent.BLOCKED
    assert classify_intent("Explain databases") == Intent.BLOCKED
    assert classify_intent("What is a column?") == Intent.BLOCKED
    assert classify_intent("Describe table metadata") == Intent.BLOCKED
    assert classify_intent("Show me database tables") == Intent.BLOCKED
    assert classify_intent("List database procedures") == Intent.BLOCKED
    assert classify_intent("Describe SQL metadata") == Intent.BLOCKED
    assert classify_intent("Get procedure metadata") == Intent.BLOCKED


def test_concrete_metadata_lookup_shape_is_still_supported():
    assert classify_intent("Find order table metadata") == Intent.METADATA_SEARCH
    assert classify_intent("Find metadata for the order_id column") == Intent.METADATA_SEARCH
    assert classify_intent("Find metadata for dbo.Customer") == Intent.METADATA_SEARCH
