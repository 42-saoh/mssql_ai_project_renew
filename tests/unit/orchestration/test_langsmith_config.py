from __future__ import annotations

from contextlib import contextmanager

from plf_agent_orchestration.langsmith_config import LangSmithSettings, LangSmithTraceContextFactory


def test_langsmith_settings_disabled_by_default(monkeypatch):
    for name in [
        "PLF_ENVIRONMENT",
        "PLF_LANGSMITH_ENABLED",
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = LangSmithSettings.from_env()

    assert settings.environment == "dev"
    assert settings.enabled is False


def test_langsmith_settings_enabled_only_in_dev(monkeypatch):
    monkeypatch.setenv("PLF_ENVIRONMENT", "dev")
    monkeypatch.setenv("PLF_LANGSMITH_ENABLED", "true")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "secret-key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "custom-dev-project")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://smith.example")

    settings = LangSmithSettings.from_env()

    assert settings.enabled is True
    assert settings.project == "custom-dev-project"
    assert settings.endpoint == "https://smith.example"


def test_langsmith_settings_requires_explicit_dev_environment(monkeypatch):
    monkeypatch.delenv("PLF_ENVIRONMENT", raising=False)
    monkeypatch.setenv("PLF_LANGSMITH_ENABLED", "true")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "secret-key")

    settings = LangSmithSettings.from_env()

    assert settings.environment == "dev"
    assert settings.enabled is False


def test_langsmith_settings_disabled_outside_dev(monkeypatch):
    monkeypatch.setenv("PLF_ENVIRONMENT", "prod")
    monkeypatch.setenv("PLF_LANGSMITH_ENABLED", "true")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "secret-key")

    settings = LangSmithSettings.from_env()

    assert settings.enabled is False


def test_langsmith_api_key_not_in_repr_or_metadata():
    settings = LangSmithSettings(
        environment="dev",
        platform_enabled=True,
        tracing_enabled=True,
        api_key="super-secret-key",
    )

    assert settings.enabled is True
    assert "super-secret-key" not in repr(settings)
    assert "super-secret-key" not in str(settings.safe_metadata({"intent": "SP_ANALYSIS"}))


def test_langsmith_noop_context_when_disabled():
    settings = LangSmithSettings(environment="dev", platform_enabled=False, tracing_enabled=True, api_key="key")
    factory = LangSmithTraceContextFactory(settings=settings)

    with factory.context(metadata={"intent": "SP_ANALYSIS"}) as value:
        assert value is None


def test_langsmith_enabled_context_uses_safe_metadata():
    calls = []

    @contextmanager
    def fake_tracing_context(**kwargs):
        calls.append(kwargs)
        yield None

    settings = LangSmithSettings(
        environment="dev",
        platform_enabled=True,
        tracing_enabled=True,
        api_key="secret",
        project="plf-dev",
    )
    factory = LangSmithTraceContextFactory(settings=settings, tracing_context=fake_tracing_context)

    with factory.context(metadata=settings.safe_metadata({"intent": "METADATA_SEARCH", "route": "metadata_gateway"})):
        pass

    assert calls == [
        {
            "enabled": True,
            "project_name": "plf-dev",
            "tags": ["plf-db-agent-v2", "orchestration", "dev"],
            "metadata": {
                "environment": "dev",
                "intent": "METADATA_SEARCH",
                "route": "metadata_gateway",
            },
        }
    ]
