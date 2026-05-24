from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STREAMLIT_ROOT = ROOT / "apps/streamlit"


def _streamlit_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in STREAMLIT_ROOT.rglob("*.py"))


def test_streamlit_code_does_not_directly_call_db_mcp_or_runner():
    text = _streamlit_text()

    forbidden_fragments = [
        "pytds",
        "python_tds",
        "pymssql",
        "sqlalchemy",
        "mssql_mcp",
        "metadata_gateway",
        "runner_app",
        "codex-runner",
        "host.docker.internal:8100",
        "localhost:8100",
        "localhost:8010",
        "/tools/",
        "/config/db-profiles",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in text


def test_streamlit_pages_use_fastapi_client_boundary():
    page_text = "\n".join(path.read_text(encoding="utf-8") for path in (STREAMLIT_ROOT / "pages").glob("*.py"))
    client_text = (STREAMLIT_ROOT / "client/api_client.py").read_text(encoding="utf-8")

    assert "ApiClient" in page_text
    assert "/api/v1/chat-runs" in client_text
    assert "requests.post" not in page_text


def test_streamlit_unsafe_action_labels_are_absent():
    text = _streamlit_text()

    for label in [
        "Execute SQL",
        "Apply DDL",
        "Deploy",
        "Run stored procedure",
        "Auto-fix database",
        "Overwrite source",
    ]:
        assert label not in text
