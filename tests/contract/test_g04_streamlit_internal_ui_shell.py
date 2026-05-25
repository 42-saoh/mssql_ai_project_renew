from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_g04_streamlit_shell_contract_files_exist():
    spec = yaml.safe_load(_read("spec/development/streamlit_internal_ui_shell.yaml"))

    assert spec["scope"] == "g04-streamlit-internal-ui-shell"
    assert (ROOT / spec["uiShell"]["entrypoint"]).exists()
    assert (ROOT / spec["uiShell"]["themeConfigPath"]).exists()
    assert (ROOT / spec["uiShell"]["cssPath"]).exists()

    for page in spec["uiShell"]["pages"].values():
        assert (ROOT / page["path"]).exists(), page["path"]


def test_g04_pages_use_declared_fastapi_client_methods():
    spec = yaml.safe_load(_read("spec/development/streamlit_internal_ui_shell.yaml"))
    client_text = _read(spec["apiBoundary"]["clientPath"])

    assert "import requests" in client_text
    assert "sqlalchemy" not in client_text
    assert "mssql_mcp" not in client_text
    assert "runner_app" not in client_text

    for endpoint in spec["apiBoundary"]["endpoints"].values():
        literal = endpoint.replace("{chatRunId}", "").replace("{conversationId}", "").replace("{artifactId}", "")
        assert literal in client_text

    for page in spec["uiShell"]["pages"].values():
        text = _read(page["path"])
        assert "ApiClient(" in text
        assert "requests." not in text
        for method in page["apiClientMethods"]:
            assert f"client.{method}(" in text


def test_g04_pages_preserve_design_and_review_states():
    spec = yaml.safe_load(_read("spec/development/streamlit_internal_ui_shell.yaml"))

    for page_name, page in spec["uiShell"]["pages"].items():
        text = _read(page["path"])
        assert "configure_page(" in text, page_name
        assert "render_sidebar(" in text, page_name
        for state in page["visibleStates"]:
            assert state in text, f"{state} missing from {page_name}"

    artifact_text = _read(spec["uiShell"]["pages"]["artifactDetail"]["path"])
    assert "productionReady" in artifact_text
    assert "reviewRequired" in artifact_text
    assert "Download preview" in artifact_text


def test_g04_shell_forbids_unsafe_action_labels():
    spec = yaml.safe_load(_read("spec/development/streamlit_internal_ui_shell.yaml"))
    streamlit_text = "\n".join(
        _read(path)
        for path in [
            spec["uiShell"]["entrypoint"],
            *(page["path"] for page in spec["uiShell"]["pages"].values()),
            spec["apiBoundary"]["clientPath"],
        ]
    )

    for label in spec["artifactReviewPolicy"]["forbiddenUnsafeLabels"]:
        assert label not in streamlit_text
