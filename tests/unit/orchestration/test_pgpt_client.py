from __future__ import annotations

import json

from plf_agent_contracts.enums import Intent
from plf_agent_orchestration.pgpt_client import (
    PGPT_ALLOWED_RESPONSE_PARAMS,
    PgptClientError,
    PgptResponsesClient,
    PgptSettings,
    build_pgpt_responses_payload,
)


def test_pgpt_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("PGPT_BASE_URL", "http://pgpt.local/v1")
    monkeypatch.setenv("PGPT_MODEL", "gpt-5.4")
    monkeypatch.setenv("PGPT_API_KEY", "secret-key")
    monkeypatch.setenv("PGPT_TIMEOUT_SECONDS", "12")

    settings = PgptSettings.from_env()

    assert settings.base_url == "http://pgpt.local/v1"
    assert settings.model == "gpt-5.4"
    assert settings.api_key == "secret-key"
    assert settings.timeout_seconds == 12
    assert settings.enabled is True


def test_pgpt_settings_disable_without_api_key(monkeypatch):
    monkeypatch.delenv("PGPT_API_KEY", raising=False)

    settings = PgptSettings.from_env()

    assert settings.model == "gpt-5.4"
    assert settings.base_url == "http://aigpt.posco.net/gspgta01-gpt/v1"
    assert settings.enabled is False


def test_pgpt_responses_payload_uses_allowed_parameters_only():
    settings = PgptSettings(api_key="key", enabled=True)

    payload = build_pgpt_responses_payload(
        settings=settings,
        input_text="PPM.dbo.X SP 분석해줘",
        instructions="Return JSON.",
        temperature=0,
        max_output_tokens=100,
    )

    assert set(payload) <= PGPT_ALLOWED_RESPONSE_PARAMS
    assert payload["model"] == "gpt-5.4"
    assert "messages" not in payload


def test_pgpt_rejects_unsupported_parameters():
    settings = PgptSettings(api_key="key", enabled=True)

    try:
        build_pgpt_responses_payload(
            settings=settings,
            input_text="message",
            instructions="instructions",
            messages=[{"role": "user", "content": "unsupported"}],
        )
    except PgptClientError as exc:
        assert exc.code == "PGPT_UNSUPPORTED_PARAMETER"
    else:  # pragma: no cover
        raise AssertionError("unsupported parameter should raise")


def test_pgpt_rejects_non_function_tools():
    settings = PgptSettings(api_key="key", enabled=True)

    try:
        build_pgpt_responses_payload(
            settings=settings,
            input_text="message",
            instructions="instructions",
            tools=[{"type": "code_interpreter"}],
        )
    except PgptClientError as exc:
        assert exc.code == "PGPT_UNSUPPORTED_TOOLS"
    else:  # pragma: no cover
        raise AssertionError("unsupported tool should raise")


def test_pgpt_classification_calls_responses_create_with_safe_payload():
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return {
                "output_text": json.dumps(
                    {
                        "intent": "DEPENDENCY_ANALYSIS",
                        "confidence": 0.91,
                        "reasonSummary": "Dependency evidence request.",
                    }
                )
            }

    class FakeOpenAI:
        responses = FakeResponses()

    client = PgptResponsesClient(
        settings=PgptSettings(api_key="secret", enabled=True),
        sdk_client=FakeOpenAI(),
    )

    result = client.classify_message("관련 dependency 알려줘")

    assert result.intent == Intent.DEPENDENCY_ANALYSIS
    assert result.confidence == 0.91
    assert result.reason_summary == "Dependency evidence request."
    assert set(captured) <= PGPT_ALLOWED_RESPONSE_PARAMS
    assert captured["model"] == "gpt-5.4"
    assert "messages" not in captured
    assert "api_key" not in captured


def test_pgpt_disabled_raises_without_sdk_call():
    client = PgptResponsesClient(settings=PgptSettings(api_key="", enabled=False))

    try:
        client.classify_message("PPM.dbo.X SP 분석해줘")
    except PgptClientError as exc:
        assert exc.code == "PGPT_DISABLED"
    else:  # pragma: no cover
        raise AssertionError("disabled PGPT should raise")
