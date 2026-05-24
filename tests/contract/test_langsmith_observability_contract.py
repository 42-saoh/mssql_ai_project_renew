from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_langsmith_observability_contract_declares_dev_only():
    spec = yaml.safe_load(
        (ROOT / "spec/observability/langsmith_development_tracing.yaml").read_text(encoding="utf-8")
    )

    assert spec["scope"] == "development-only"
    assert spec["defaultEnabled"] is False
    assert spec["activation"]["allRequired"]["PLF_ENVIRONMENT"] == "dev"
    assert spec["activation"]["allRequired"]["PLF_LANGSMITH_ENABLED"] == "true"
    assert spec["activation"]["allRequired"]["LANGSMITH_TRACING"] == "true"
    assert spec["activation"]["allRequired"]["LANGSMITH_API_KEY"] == "present"
    assert spec["behavior"]["productionAlwaysDisabled"] is True


def test_langsmith_contract_forbids_raw_and_secret_trace_data():
    spec = yaml.safe_load(
        (ROOT / "spec/observability/langsmith_development_tracing.yaml").read_text(encoding="utf-8")
    )
    forbidden = set(spec["forbiddenTraceData"])

    assert "raw prompt" in forbidden
    assert "raw provider response" in forbidden
    assert "row data" in forbidden
    assert "api keys" in forbidden
