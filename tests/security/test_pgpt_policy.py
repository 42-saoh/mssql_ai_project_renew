from __future__ import annotations

from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_orchestration.pgpt_client import PgptClassification, PgptSettings


class EchoReasonPgpt:
    settings = PgptSettings(api_key="super-secret-key", enabled=True)

    def classify_message(self, message: str):
        return PgptClassification(
            intent=Intent.SP_ANALYSIS,
            confidence=0.99,
            reason_summary=message,
        )


def test_pgpt_result_does_not_expose_api_key():
    result = orchestrate_message("PPM.dbo.X SP 분석해줘", pgpt_client=EchoReasonPgpt())

    assert "super-secret-key" not in str(result)
    assert "PPM.dbo.X SP 분석해줘" not in str(result)


def test_pgpt_reason_summary_does_not_expose_raw_provider_payload():
    result = orchestrate_message("PPM.dbo.X SP 분석해줘", pgpt_client=EchoReasonPgpt())

    assert "raw_provider" not in str(result).lower()
    assert "api_key" not in str(result).lower()
