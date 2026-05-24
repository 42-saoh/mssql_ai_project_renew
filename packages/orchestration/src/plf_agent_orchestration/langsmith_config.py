from __future__ import annotations

import os
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any

LANGSMITH_DEFAULT_PROJECT = "plf-db-agent-v2-dev"
LANGSMITH_DEFAULT_ENDPOINT = "https://api.smith.langchain.com"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LangSmithSettings:
    environment: str = "dev"
    environment_configured: bool = True
    platform_enabled: bool = False
    tracing_enabled: bool = False
    api_key: str = field(default="", repr=False)
    project: str = LANGSMITH_DEFAULT_PROJECT
    endpoint: str = LANGSMITH_DEFAULT_ENDPOINT

    @classmethod
    def from_env(cls) -> "LangSmithSettings":
        raw_environment = os.getenv("PLF_ENVIRONMENT")
        return cls(
            environment=(raw_environment or "dev").strip() or "dev",
            environment_configured=raw_environment is not None,
            platform_enabled=_env_flag("PLF_LANGSMITH_ENABLED", default=False),
            tracing_enabled=_env_flag("LANGSMITH_TRACING", default=False),
            api_key=os.getenv("LANGSMITH_API_KEY", "").strip(),
            project=os.getenv("LANGSMITH_PROJECT", LANGSMITH_DEFAULT_PROJECT).strip() or LANGSMITH_DEFAULT_PROJECT,
            endpoint=os.getenv("LANGSMITH_ENDPOINT", LANGSMITH_DEFAULT_ENDPOINT).strip() or LANGSMITH_DEFAULT_ENDPOINT,
        )

    @property
    def enabled(self) -> bool:
        return (
            self.environment == "dev"
            and self.environment_configured
            and self.platform_enabled
            and self.tracing_enabled
            and bool(self.api_key)
        )

    def safe_tags(self) -> list[str]:
        return ["plf-db-agent-v2", "orchestration", self.environment]

    def safe_metadata(self, result: dict[str, Any] | None = None) -> dict[str, Any]:
        metadata: dict[str, Any] = {"environment": self.environment}
        if not result:
            return metadata
        for key in [
            "intent",
            "policyDecision",
            "route",
            "pgptUsed",
            "pgptModel",
            "pgptFallbackReason",
        ]:
            if key not in result:
                continue
            value = result.get(key)
            if isinstance(value, str | bool | int | float) or value is None:
                metadata[key] = value
        return metadata


class LangSmithTraceContextFactory:
    def __init__(self, settings: LangSmithSettings | None = None, tracing_context: Any | None = None):
        self.settings = settings or LangSmithSettings.from_env()
        self._tracing_context = tracing_context

    @classmethod
    def from_env(cls) -> "LangSmithTraceContextFactory":
        return cls(LangSmithSettings.from_env())

    def context(self, *, metadata: dict[str, Any] | None = None):
        if not self.settings.enabled:
            return nullcontext()
        tracing_context = self._tracing_context or self._load_tracing_context()
        return tracing_context(
            enabled=True,
            project_name=self.settings.project,
            tags=self.settings.safe_tags(),
            metadata=metadata or self.settings.safe_metadata(),
        )

    def _load_tracing_context(self):
        try:
            import langsmith as ls
        except Exception:
            return lambda **kwargs: nullcontext()
        return ls.tracing_context
