from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from plf_agent_contracts.enums import Intent
from plf_agent_orchestration import graph
from plf_agent_orchestration.pgpt_client import PgptClassification, PgptSettings


class RoutePgpt:
    def __init__(self):
        self.settings = PgptSettings(api_key="secret", enabled=True)
        self.calls: list[str] = []

    def classify_message(self, message: str):
        self.calls.append(message)
        return PgptClassification(
            intent=Intent.SP_ANALYSIS,
            confidence=0.95,
            reason_summary="Stored procedure analysis request.",
        )


def test_chat_run_keeps_shape_and_can_use_pgpt(monkeypatch):
    pgpt = RoutePgpt()
    monkeypatch.setattr(graph.PgptResponsesClient, "from_env", staticmethod(lambda: pgpt))

    response = TestClient(create_app()).post(
        "/api/v1/chat-runs",
        json={"message": "PPM.dbo.X SP 분석해줘"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ACCEPTED"
    assert body["intent"] == "SP_ANALYSIS"
    assert body["route"] == "codex_runner"
    assert body["pgptUsed"] is True
    assert body["pgptModel"] == "gpt-5.4"
    assert "chatRunId" in body
    assert "conversationId" in body
    assert pgpt.calls == ["PPM.dbo.X SP 분석해줘"]


def test_chat_run_blocks_general_chat_before_pgpt(monkeypatch):
    pgpt = RoutePgpt()
    monkeypatch.setattr(graph.PgptResponsesClient, "from_env", staticmethod(lambda: pgpt))

    response = TestClient(create_app()).post(
        "/api/v1/chat-runs",
        json={"message": "오늘 점심 추천해줘"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "BLOCKED"
    assert body["intent"] == "BLOCKED"
    assert body["pgptUsed"] is False
    assert body["pgptFallbackReason"] == "POLICY_BLOCKED_BEFORE_PGPT"
    assert pgpt.calls == []
