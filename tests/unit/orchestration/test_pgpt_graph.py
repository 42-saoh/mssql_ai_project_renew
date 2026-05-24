from __future__ import annotations

from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_orchestration.pgpt_client import PgptClassification, PgptClientError, PgptSettings


class FakePgptClient:
    def __init__(self, classification=None, error=None):
        self.settings = PgptSettings(api_key="secret-value", enabled=True)
        self.classification = classification
        self.error = error
        self.calls = []

    def classify_message(self, message: str):
        self.calls.append(message)
        if self.error:
            raise self.error
        return self.classification


def test_orchestration_can_use_pgpt_for_allowed_db_request():
    pgpt = FakePgptClient(
        PgptClassification(
            intent=Intent.DEPENDENCY_ANALYSIS,
            confidence=0.9,
            reason_summary="Dependency evidence request.",
        )
    )

    result = orchestrate_message("이 컬럼 dependency 알려줘", pgpt_client=pgpt)

    assert result["intent"] == "DEPENDENCY_ANALYSIS"
    assert result["route"] == "codex_runner"
    assert result["pgptUsed"] is True
    assert result["pgptModel"] == "gpt-5.4"
    assert result["pgptFallbackReason"] is None
    assert result["pgptReasonSummary"] == "Dependency evidence request."
    assert pgpt.calls == ["이 컬럼 dependency 알려줘"]


def test_orchestration_falls_back_when_pgpt_fails():
    pgpt = FakePgptClient(error=PgptClientError("PGPT_INVALID_RESPONSE", "bad response"))

    result = orchestrate_message("PPM.dbo.X SP 분석해줘", pgpt_client=pgpt)

    assert result["intent"] == "SP_ANALYSIS"
    assert result["route"] == "codex_runner"
    assert result["pgptUsed"] is False
    assert result["pgptFallbackReason"] == "PGPT_INVALID_RESPONSE"


def test_orchestration_does_not_call_pgpt_for_general_chat():
    pgpt = FakePgptClient(
        PgptClassification(
            intent=Intent.METADATA_SEARCH,
            confidence=0.9,
            reason_summary="Should not be used.",
        )
    )

    result = orchestrate_message("오늘 점심 추천해줘", pgpt_client=pgpt)

    assert result["intent"] == "BLOCKED"
    assert result["route"] == "blocked"
    assert result["pgptUsed"] is False
    assert result["pgptFallbackReason"] == "POLICY_BLOCKED_BEFORE_PGPT"
    assert pgpt.calls == []


def test_orchestration_sanitizes_pgpt_reason_summary_echo():
    message = "PPM.dbo.X SP 분석해줘"
    pgpt = FakePgptClient(
        PgptClassification(
            intent=Intent.SP_ANALYSIS,
            confidence=0.9,
            reason_summary=message,
        )
    )

    result = orchestrate_message(message, pgpt_client=pgpt)

    assert result["pgptUsed"] is True
    assert result["pgptReasonSummary"] == "PGPT classified the DB analysis request."
