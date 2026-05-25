from __future__ import annotations

import pytest

from apps.api.api_app.services.mssql_mcp_client import (
    ALLOWED_METADATA_TOOL_NAMES,
    MssqlMcpClient,
    MssqlMcpClientError,
    is_allowed_metadata_tool_name,
    is_blocked_mcp_tool_name,
)


def test_allowed_metadata_tools_do_not_include_execution_or_mutation_names():
    forbidden_fragments = (
        "execute",
        "apply",
        "deploy",
        "row_data",
        "free_sql",
        "insert",
        "update",
        "delete",
        "drop",
        "truncate",
        "backup",
        "restore",
    )

    for tool_name in ALLOWED_METADATA_TOOL_NAMES:
        assert is_allowed_metadata_tool_name(tool_name)
        assert not any(fragment in tool_name for fragment in forbidden_fragments)


@pytest.mark.parametrize(
    "tool_name",
    [
        "execute_sql",
        "execute-procedure",
        "apply_ddl",
        "deploy_source",
        "query_row_data",
        "free_sql_runner",
        "create_table",
        "alter_table",
        "drop_table",
        "truncate_table",
        "insert_row",
        "update_row",
        "delete_row",
        "merge_rows",
        "grant_permission",
        "revoke_permission",
        "unknown_metadata_export",
    ],
)
def test_execution_mutation_and_unknown_tools_are_blocked(tool_name):
    assert is_blocked_mcp_tool_name(tool_name) or not is_allowed_metadata_tool_name(tool_name)


def test_safe_error_from_blocked_tool_omits_raw_arguments():
    try:
        MssqlMcpClient(transport=lambda method, path, payload: {"ok": True}).invoke_tool(
            "execute_sql",
            {"sql": "select * from dbo.Customer", "password": "abc"},
        )
    except MssqlMcpClientError as exc:
        response = exc.to_response()
    else:  # pragma: no cover
        raise AssertionError("blocked tool should raise")

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_TOOL_BLOCKED"
    assert "select *" not in rendered
    assert "password" not in rendered
    assert "abc" not in rendered


def test_safe_error_from_blocked_tool_name_omits_unsafe_tool_text():
    try:
        MssqlMcpClient(transport=lambda method, path, payload: {"ok": True}).invoke_tool(
            "execute_sql password=abc select * from dbo.Customer",
            {"dbProfileId": "master"},
        )
    except MssqlMcpClientError as exc:
        response = exc.to_response()
    else:  # pragma: no cover
        raise AssertionError("blocked tool should raise")

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_TOOL_BLOCKED"
    assert response["error"]["details"]["toolName"] == "<redacted>"
    assert "select *" not in rendered
    assert "password" not in rendered
    assert "abc" not in rendered


def test_unsafe_external_response_is_not_returned_to_platform():
    def transport(method, path, payload):
        return {
            "ok": True,
            "toolName": "search_metadata_objects",
            "data": {"rows": [{"customer": "alice"}], "sample": "select * from dbo.Customer"},
        }

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(
            "search_metadata_objects",
            {"dbProfileId": "master", "query": "customer"},
        )

    assert exc_info.value.code == "MCP_RESPONSE_BLOCKED"
    response = exc_info.value.to_response()
    rendered = str(response).lower()
    assert "select *" not in rendered
    assert "alice" not in rendered
    assert "ROW_DATA" in response["error"]["details"]["violations"]


def test_connection_string_external_diagnostic_is_not_returned_to_platform():
    def transport(method, path, payload):
        return {
            "ok": True,
            "toolName": "search_metadata_objects",
            "diagnostics": "Server=tcp:prod;Database=ERP;Integrated Security=True;",
        }

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(
            "search_metadata_objects",
            {"dbProfileId": "master", "query": "customer"},
        )

    assert exc_info.value.code == "MCP_RESPONSE_BLOCKED"
    response = exc_info.value.to_response()
    rendered = str(response).lower()
    assert "server=" not in rendered
    assert "erp" not in rendered
    assert "CONNECTION_STRING" in response["error"]["details"]["violations"]
