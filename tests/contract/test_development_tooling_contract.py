from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_context7_and_playwright_skills_exist_and_are_referenced():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert (ROOT / ".agents/skills/context7-docs/SKILL.md").exists()
    assert (ROOT / ".agents/skills/browser-automation-smoke/SKILL.md").exists()
    assert "context7-docs" in agents
    assert "browser-automation-smoke" in agents


def test_development_tooling_contract_declares_dev_only_boundaries():
    spec = yaml.safe_load((ROOT / "spec/development/context7_playwright_tooling.yaml").read_text(encoding="utf-8"))

    assert spec["scope"] == "development-only"
    assert spec["sourceSkills"]["context7"] == ".agents/skills/context7-docs/SKILL.md"
    assert spec["sourceSkills"]["playwright"] == ".agents/skills/browser-automation-smoke/SKILL.md"
    assert spec["context7"]["activation"]["allRequired"]["PLF_ENVIRONMENT"] == "dev"
    assert spec["context7"]["activation"]["allRequired"]["CONTEXT7_API_KEY"] == "present"
    assert spec["playwright"]["activation"]["allRequired"]["PLF_PLAYWRIGHT_SMOKE_ENABLED"] == "true"
    assert spec["playwright"]["smokeContract"]["destructiveActionsAllowed"] is False
    assert spec["playwright"]["smokeContract"]["storageStateCommitted"] is False
    assert spec["realmBoundary"]["inheritedByServiceCodexRunnerRuntime"] is False


def test_development_tooling_env_defaults_are_safe():
    values = _env_values()

    assert values["PLF_CONTEXT7_ENABLED"] == "false"
    assert values["CONTEXT7_API_KEY"] == ""
    assert values["PLF_PLAYWRIGHT_SMOKE_ENABLED"] == "false"
    assert values["PLAYWRIGHT_BASE_URL"] == "http://127.0.0.1:8501"
    assert values["PLAYWRIGHT_BROWSER"] == "chromium"
    assert values["PLAYWRIGHT_HEADLESS"] == "true"
    assert values["PLAYWRIGHT_BROWSERS_PATH"] == ""


def test_playwright_dependencies_are_exactly_pinned():
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()

    assert "playwright==1.60.0" in requirements
    assert "pytest-playwright==0.8.0" in requirements


def test_tooling_reference_doc_declares_forbidden_data():
    text = (ROOT / "docs/reference/development-tooling-context7-playwright.md").read_text(encoding="utf-8")

    assert "CONTEXT7_API_KEY=" in text
    assert "PLF_PLAYWRIGHT_SMOKE_ENABLED=false" in text
    assert "Do not send secrets" in text
    assert "Do not commit screenshots" in text
