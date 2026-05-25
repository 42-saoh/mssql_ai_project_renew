from __future__ import annotations

import urllib.error
from io import BytesIO

import pytest

from apps.api.api_app.services.mssql_mcp_client import (
    ALLOWED_METADATA_TOOL_NAMES,
    MssqlMcpClient,
    MssqlMcpClientError,
    is_allowed_metadata_tool_name,
)


def test_catalog_filters_to_explicit_readonly_allowlist():
    def transport(method, path, payload):
        return {
            "tools": [
                {"name": "search_metadata_objects", "readOnly": True},
                {"name": "get_table_schema", "readOnly": True},
                {"name": "execute_sql", "readOnly": False},
                {"name": "drop_table", "readOnly": False},
                {"name": "unknown_readonly_tool", "readOnly": True},
                {"name": "get_table_columns"},
            ]
        }

    catalog = MssqlMcpClient(transport=transport).list_tools()

    assert [tool["name"] for tool in catalog["tools"]] == [
        "search_metadata_objects",
        "get_table_schema",
    ]
    assert catalog["policy"]["readOnlyMetadataOnly"] is True
    assert catalog["policy"]["filteredToolCount"] == 4
    assert set(catalog["policy"]["allowedToolNames"]) == ALLOWED_METADATA_TOOL_NAMES


@pytest.mark.parametrize(
    "tool_name",
    [
        "execute_sql",
        "execute_procedure",
        "query_row_data",
        "drop_table",
        "insert_row",
        "update_row",
        "delete_row",
        "backup_database",
        "unknown_readonly_tool",
    ],
)
def test_blocked_or_unknown_tools_fail_before_transport(tool_name):
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(tool_name, {"dbProfileId": "master"})

    assert exc_info.value.code == "MCP_TOOL_BLOCKED"
    assert exc_info.value.status_code == 403
    assert calls == []


@pytest.mark.parametrize("tool_name", sorted(ALLOWED_METADATA_TOOL_NAMES))
def test_allowed_metadata_tool_names_are_not_classified_as_blocked(tool_name):
    assert is_allowed_metadata_tool_name(tool_name)


@pytest.mark.parametrize(
    ("arguments", "violation"),
    [
        ({"dbProfileId": "master", "query": "select * from users"}, "ROW_DATA"),
        ({"dbProfileId": "master", "query": "drop table dbo.X"}, "DDL_DML_APPLY"),
        ({"dbProfileId": "master", "query": "execute dbo.ProcessOrder"}, "SQL_EXECUTION"),
        ({"dbProfileId": "master", "rawPrompt": "hello"}, "RAW_PROMPT"),
        ({"dbProfileId": "master", "password": "secret"}, "SECRET"),
    ],
)
def test_unsafe_arguments_fail_before_transport(arguments, violation):
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool("search_metadata_objects", arguments)

    assert exc_info.value.code == "MCP_ARGUMENTS_BLOCKED"
    assert violation in exc_info.value.details["violations"]
    assert calls == []


@pytest.mark.parametrize("limit", [0, 101])
def test_metadata_search_rejects_out_of_range_limits_before_transport(limit):
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True, "toolName": "search_metadata_objects", "data": {"items": []}}

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).search_metadata("order", limit=limit)

    assert exc_info.value.code == "MCP_ARGUMENTS_BLOCKED"
    assert exc_info.value.details["field"] == "limit"
    assert calls == []


def test_tool_success_response_must_match_requested_tool_name():
    def transport(method, path, payload):
        return {"ok": True, "toolName": "get_table_schema", "data": {}}

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool("search_metadata_objects", {"dbProfileId": "master", "query": "order"})

    assert exc_info.value.code == "MCP_INVALID_RESPONSE"
    assert exc_info.value.details["responseToolName"] == "get_table_schema"


@pytest.mark.parametrize(
    ("response", "violation"),
    [
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"sample": "select * from users"}}, "ROW_DATA"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"password": "abc"}}, "SECRET"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"definition": "create procedure dbo.X as select 1"}}, "RAW_SP"),
    ],
)
def test_unsafe_external_responses_fail_closed(response, violation):
    def transport(method, path, payload):
        return response

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool("search_metadata_objects", {"dbProfileId": "master", "query": "order"})

    assert exc_info.value.code == "MCP_RESPONSE_BLOCKED"
    assert violation in exc_info.value.details["violations"]


def test_http_error_body_is_sanitized_before_platform_response():
    body = b'{"error":{"code":"BAD_SQL","message":"cannot execute select * from users","details":{"password":"abc"}}}'
    error = urllib.error.HTTPError(
        url="http://mcp.example/tools/search_metadata_objects/invoke",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=BytesIO(body),
    )

    safe_error = MssqlMcpClient()._http_error("/tools/search_metadata_objects/invoke", error)
    response = safe_error.to_response()

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_HTTP_ERROR"
    assert "select *" not in rendered
    assert "password" not in rendered
    assert "abc" not in rendered
    assert response["error"]["details"] == {
        "path": "/tools/search_metadata_objects/invoke",
        "httpStatus": 400,
    }
