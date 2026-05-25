from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.api_app.main import create_app
from apps.api.api_app.services import metadata_service
from apps.api.api_app.services.mssql_mcp_client import MssqlMcpClient


def test_blocked_metadata_tool_route_returns_safe_error_before_proxy():
    response = TestClient(create_app()).post(
        "/api/v1/metadata/tools/execute_sql/invoke",
        json={"arguments": {"dbProfileId": "master", "sql": "select * from users"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "MCP_TOOL_BLOCKED"
    assert "select *" not in str(body).lower()


def test_metadata_search_route_blocks_unsafe_query_before_proxy():
    response = TestClient(create_app()).get("/api/v1/metadata/search?q=drop%20table%20dbo.X")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "MCP_ARGUMENTS_BLOCKED"
    assert "drop table" not in str(body).lower()


def test_metadata_tools_route_filters_external_catalog(monkeypatch):
    def transport(method, path, payload):
        return {
            "tools": [
                {"name": "search_metadata_objects", "readOnly": True},
                {"name": "execute_sql", "readOnly": False},
                {"name": "unknown_readonly_tool", "readOnly": True},
            ]
        }

    monkeypatch.setattr(
        metadata_service,
        "get_mssql_mcp_client",
        lambda: MssqlMcpClient(transport=transport),
    )

    response = TestClient(create_app()).get("/api/v1/metadata/tools")

    assert response.status_code == 200
    body = response.json()
    assert [tool["name"] for tool in body["tools"]] == ["search_metadata_objects"]
    assert body["policy"]["filteredToolCount"] == 2
