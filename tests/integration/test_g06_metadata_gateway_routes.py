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
    assert "toolName" not in body
    assert "data" not in body
    assert "drop table" not in str(body).lower()


def test_metadata_search_route_blocks_free_sql_phrase_with_safe_error_envelope():
    response = TestClient(create_app()).get(
        "/api/v1/metadata/search",
        params={"q": "run query for customer metadata"},
    )

    assert response.status_code == 200
    body = response.json()
    rendered = str(body).lower()
    assert body["ok"] is False
    assert body["error"]["code"] == "MCP_ARGUMENTS_BLOCKED"
    assert body["error"]["message"] == "MCP arguments contain content blocked by platform redaction policy."
    assert "FREE_SQL_EXECUTION_BLOCKED" in body["error"]["details"]["violations"]
    assert "toolName" not in body
    assert "data" not in body
    assert "run query" not in rendered


@pytest.mark.parametrize(
    "query",
    [
        "run stored procedure dbo.ProcessOrder",
        "call procedure dbo.ProcessOrder",
        "프로시저를 실행해줘",
        "저장 프로시저를 호출해줘",
    ],
)
def test_metadata_search_route_blocks_stored_procedure_execution_phrases_before_proxy(query):
    response = TestClient(create_app()).get("/api/v1/metadata/search", params={"q": query})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "MCP_ARGUMENTS_BLOCKED"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in body["error"]["details"]["violations"]
    assert query not in str(body)


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


def test_metadata_search_route_fails_closed_when_external_success_omits_ok(monkeypatch):
    def transport(method, path, payload):
        return {"toolName": "search_metadata_objects", "data": {"items": []}}

    monkeypatch.setattr(
        metadata_service,
        "get_mssql_mcp_client",
        lambda: MssqlMcpClient(transport=transport),
    )

    response = TestClient(create_app()).get("/api/v1/metadata/search", params={"q": "order"})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "MCP_INVALID_RESPONSE"
    assert "toolName" not in body
    assert "data" not in body


def test_metadata_tool_invoke_route_normalizes_external_error_envelope(monkeypatch):
    def transport(method, path, payload):
        return {
            "ok": False,
            "toolName": "get_table_schema",
            "data": {"ignored": True},
            "error": {
                "code": "NOT_FOUND",
                "message": "Object was not found.",
                "details": {"retryable": False},
                "extra": "ignored",
            },
        }

    monkeypatch.setattr(
        metadata_service,
        "get_mssql_mcp_client",
        lambda: MssqlMcpClient(transport=transport),
    )

    response = TestClient(create_app()).post(
        "/api/v1/metadata/tools/get_table_schema/invoke",
        json={"arguments": {"dbProfileId": "master", "schema": "dbo", "tableName": "TB_ORDER"}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "NOT_FOUND",
            "message": "Object was not found.",
            "details": {"retryable": False},
        },
    }
