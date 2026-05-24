from __future__ import annotations

from apps.api.api_app.services.mssql_mcp_client import (
    MssqlMcpClient,
    MssqlMcpClientError,
    is_blocked_mcp_tool_name,
)


def test_client_builds_expected_urls():
    client = MssqlMcpClient(base_url="http://mcp.example/")
    assert client._url("/health/ready") == "http://mcp.example/health/ready"
    assert client._url("catalog/tools") == "http://mcp.example/catalog/tools"


def test_runtime_catalog_pass_through():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"tools": [{"name": "search_metadata_objects", "readOnly": True}]}

    result = MssqlMcpClient(transport=transport).list_tools()

    assert result["tools"][0]["name"] == "search_metadata_objects"
    assert calls == [("GET", "/catalog/tools", None)]


def test_invoke_tool_payload_shape():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True, "toolName": "get_table_schema"}

    result = MssqlMcpClient(transport=transport).invoke_tool(
        "get_table_schema",
        {"dbProfileId": "master", "schema": "dbo", "tableName": "TB_ORDER"},
    )

    assert result["ok"] is True
    assert calls == [
        (
            "POST",
            "/tools/get_table_schema/invoke",
            {
                "arguments": {
                    "dbProfileId": "master",
                    "schema": "dbo",
                    "tableName": "TB_ORDER",
                }
            },
        )
    ]


def test_metadata_search_maps_to_external_search_tool():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True, "toolName": "search_metadata_objects", "data": {"items": []}}

    MssqlMcpClient(transport=transport).search_metadata("order", db_profile_id="ppm", limit=7)

    assert calls == [
        (
            "POST",
            "/tools/search_metadata_objects/invoke",
            {"arguments": {"dbProfileId": "ppm", "query": "order", "limit": 7}},
        )
    ]


def test_blocked_names_are_caught_before_transport():
    assert is_blocked_mcp_tool_name("apply_ddl")
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    client = MssqlMcpClient(transport=transport)

    try:
        client.invoke_tool("apply_ddl", {"dbProfileId": "master"})
    except MssqlMcpClientError as exc:
        assert exc.status_code == 403
        assert exc.to_response()["error"]["code"] == "MCP_TOOL_BLOCKED"
    else:  # pragma: no cover
        raise AssertionError("blocked MCP tool did not raise")

    assert calls == []


def test_blocked_arguments_are_caught_before_transport():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    client = MssqlMcpClient(transport=transport)

    try:
        client.invoke_tool("search_metadata_objects", {"dbProfileId": "master", "query": "select * from users"})
    except MssqlMcpClientError as exc:
        assert exc.status_code == 400
        assert "ROW_DATA" in exc.to_response()["error"]["details"]["violations"]
    else:  # pragma: no cover
        raise AssertionError("blocked MCP arguments did not raise")

    assert calls == []


def test_unavailable_error_is_safe_response():
    error = MssqlMcpClientError(
        "MCP_UNAVAILABLE",
        "External MSSQL MCP is unavailable.",
        details={"path": "/health/ready", "timeoutSeconds": 10, "errorClass": "URLError"},
    )

    response = error.to_response()

    assert response == {
        "ok": False,
        "error": {
            "code": "MCP_UNAVAILABLE",
            "message": "External MSSQL MCP is unavailable.",
            "details": {
                "path": "/health/ready",
                "timeoutSeconds": 10,
                "errorClass": "URLError",
            },
        },
    }
