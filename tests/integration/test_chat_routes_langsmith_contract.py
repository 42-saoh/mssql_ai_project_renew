from __future__ import annotations

from contextlib import nullcontext

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from plf_agent_orchestration import graph
from plf_agent_orchestration.langsmith_config import LangSmithSettings, LangSmithTraceContextFactory


class CapturingLangSmithTrace(LangSmithTraceContextFactory):
    def __init__(self):
        super().__init__(
            settings=LangSmithSettings(
                environment="dev",
                platform_enabled=True,
                tracing_enabled=True,
                api_key="secret-key",
                project="plf-dev",
            ),
            tracing_context=lambda **kwargs: nullcontext(),
        )
        self.metadata = []

    def context(self, *, metadata=None):
        self.metadata.append(metadata or {})
        return super().context(metadata=metadata)


def test_chat_run_shape_with_langsmith_trace(monkeypatch):
    trace = CapturingLangSmithTrace()
    monkeypatch.setattr(graph.LangSmithTraceContextFactory, "from_env", staticmethod(lambda: trace))

    response = TestClient(create_app()).post(
        "/api/v1/chat-runs",
        json={"message": "PPM.dbo.X SP 분석해줘"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "SP_ANALYSIS"
    assert "chatRunId" in body
    assert "conversationId" in body
    assert trace.metadata
    assert trace.metadata[0]["intent"] == "SP_ANALYSIS"
    assert trace.metadata[0]["route"] == "codex_runner"


def test_blocked_chat_trace_metadata_is_safe(monkeypatch):
    trace = CapturingLangSmithTrace()
    monkeypatch.setattr(graph.LangSmithTraceContextFactory, "from_env", staticmethod(lambda: trace))

    response = TestClient(create_app()).post(
        "/api/v1/chat-runs",
        json={"message": "오늘 점심 추천해줘"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "BLOCKED"
    assert trace.metadata[0]["intent"] == "BLOCKED"
    assert "오늘 점심 추천해줘" not in str(trace.metadata)
    assert "secret-key" not in str(trace.metadata)
