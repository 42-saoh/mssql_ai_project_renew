from __future__ import annotations

from contextlib import nullcontext

from plf_agent_orchestration.graph import orchestrate_message
from plf_agent_orchestration.langsmith_config import LangSmithSettings, LangSmithTraceContextFactory


class CapturingTrace(LangSmithTraceContextFactory):
    def __init__(self):
        super().__init__(
            settings=LangSmithSettings(
                environment="dev",
                platform_enabled=True,
                tracing_enabled=True,
                api_key="langsmith-secret",
            ),
            tracing_context=lambda **kwargs: nullcontext(),
        )
        self.metadata = []

    def context(self, *, metadata=None):
        self.metadata.append(metadata or {})
        return super().context(metadata=metadata)


def test_langsmith_metadata_does_not_include_api_key_or_raw_prompt():
    trace = CapturingTrace()

    result = orchestrate_message("PPM.dbo.X SP 분석해줘", langsmith_trace=trace)

    assert "langsmith-secret" not in str(result)
    assert "langsmith-secret" not in str(trace.metadata)
    assert "PPM.dbo.X SP 분석해줘" not in str(trace.metadata)


def test_langsmith_metadata_does_not_include_raw_provider_response_terms():
    trace = CapturingTrace()

    result = orchestrate_message("PPM.dbo.X SP 분석해줘", langsmith_trace=trace)

    assert "raw_provider" not in str(result).lower()
    assert "raw_provider" not in str(trace.metadata).lower()
    assert "api_key" not in str(trace.metadata).lower()
