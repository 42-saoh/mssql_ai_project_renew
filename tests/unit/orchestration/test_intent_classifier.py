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
