from __future__ import annotations

from pathlib import Path
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_development_docs_require_design_md_for_streamlit_work():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = (ROOT / ".agents/skills/v2-streamlit-chat-ui/SKILL.md").read_text(encoding="utf-8")

    assert "DESIGN.md" in agents
    assert "Streamlit UI" in agents
    assert "DESIGN.md" in skill


def test_streamlit_design_contract_declares_source_and_boundaries():
    spec = yaml.safe_load((ROOT / "spec/ui/streamlit_design_contract.yaml").read_text(encoding="utf-8"))

    assert spec["source"] == "DESIGN.md"
    assert spec["required"]["themeConfigPath"] == ".streamlit/config.toml"
    assert spec["required"]["cssPath"] == "styles/design.css"
    assert spec["apiBoundary"]["streamlitMayCall"] == "FastAPI only"
    assert spec["realmBoundary"]["designMdInheritedByRuntimeTemplate"] is False
    assert "Execute SQL" in spec["generatedOutputPolicy"]["forbiddenUnsafeLabels"]


def test_streamlit_theme_maps_design_tokens():
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8"))
    theme = config["theme"]

    assert theme["primaryColor"] == "#000000"
    assert theme["backgroundColor"] == "#ffffff"
    assert theme["secondaryBackgroundColor"] == "#f3f3f3"
    assert theme["buttonRadius"] == "999px"
    assert theme["showSidebarBorder"] is True


def test_streamlit_design_css_uses_required_stable_utilities():
    css = (ROOT / "styles/design.css").read_text(encoding="utf-8")

    for class_name in [
        "agent-card",
        "agent-card-soft",
        "agent-dark-band",
        "agent-badge",
        "agent-badge-draft",
        "agent-badge-warning",
        "agent-badge-success",
        "agent-badge-danger",
        "agent-badge-info",
        "agent-code-label",
    ]:
        assert f".{class_name}" in css

    assert ".st-" not in css
    assert "css-" not in css
