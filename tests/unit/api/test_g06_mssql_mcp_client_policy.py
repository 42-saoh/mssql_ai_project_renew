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


def test_catalog_filters_blocked_tools_before_unsafe_response_validation():
    def transport(method, path, payload):
        return {
            "tools": [
                {"name": "search_metadata_objects", "readOnly": True},
                {
                    "name": "execute_sql",
                    "readOnly": False,
                    "description": "execute select * from dbo.Customer with password=abc",
                },
                {
                    "name": "drop_table",
                    "readOnly": False,
                    "description": "drop table dbo.Customer",
                },
            ]
        }

    catalog = MssqlMcpClient(transport=transport).list_tools()

    rendered = str(catalog).lower()
    assert [tool["name"] for tool in catalog["tools"]] == ["search_metadata_objects"]
    assert catalog["policy"]["filteredToolCount"] == 2
    assert "select *" not in rendered
    assert "password" not in rendered
    assert "drop table" not in rendered


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
        ({"dbProfileId": "master", "query": "select name from dbo.Customer"}, "ROW_DATA"),
        ({"dbProfileId": "master", "query": "drop table dbo.X"}, "DDL_DML_APPLY"),
        ({"dbProfileId": "master", "query": "execute dbo.ProcessOrder"}, "SQL_EXECUTION"),
        (
            {"dbProfileId": "master", "query": "run stored procedure dbo.ProcessOrder"},
            "STORED_PROCEDURE_EXECUTION_BLOCKED",
        ),
        (
            {"dbProfileId": "master", "query": "call procedure dbo.ProcessOrder"},
            "STORED_PROCEDURE_EXECUTION_BLOCKED",
        ),
        (
            {"dbProfileId": "master", "query": "프로시저를 실행해줘"},
            "STORED_PROCEDURE_EXECUTION_BLOCKED",
        ),
        (
            {"dbProfileId": "master", "query": "저장 프로시저를 호출해줘"},
            "STORED_PROCEDURE_EXECUTION_BLOCKED",
        ),
        ({"dbProfileId": "master", "rawPrompt": "hello"}, "RAW_PROMPT"),
        ({"dbProfileId": "master", "password": "secret"}, "SECRET"),
        ({"dbProfileId": "master", "procedureDefinition": "AS BEGIN SELECT 1 END"}, "RAW_SP"),
        (
            {"dbProfileId": "master", "query": "Server=tcp:prod;Database=ERP;Integrated Security=True;"},
            "CONNECTION_STRING",
        ),
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


@pytest.mark.parametrize(
    ("query", "violation"),
    [
        ("run query for customer metadata", "FREE_SQL_EXECUTION_BLOCKED"),
        ("free SQL execution for metadata lookup", "FREE_SQL_EXECUTION_BLOCKED"),
        ("run this DDL for dbo.Customer", "DDL_DML_APPLY_BLOCKED"),
        ("deploy source for the mapper", "SOURCE_APPLY_OR_DEPLOY_BLOCKED"),
        ("show actual rows for dbo.Customer", "ROW_DATA_ACCESS_BLOCKED"),
    ],
)
def test_forbidden_operation_argument_codes_block_allowed_tools_before_transport(query, violation):
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(
            "search_metadata_objects",
            {"dbProfileId": "master", "query": query},
        )

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
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"rows": [{"customer": "alice"}]}}, "ROW_DATA"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"records": [{"customer": "alice"}]}}, "ROW_DATA"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"password": "abc"}}, "SECRET"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"definition": "create procedure dbo.X as select 1"}}, "RAW_SP"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"procedureDefinition": "AS BEGIN SELECT 1 END"}}, "RAW_SP"),
        ({"ok": True, "toolName": "search_metadata_objects", "data": {"definition": "AS BEGIN SELECT 1 END"}}, "RAW_SP"),
        (
            {
                "ok": True,
                "toolName": "get_procedure_definition",
                "data": {"body": "AS BEGIN SET NOCOUNT ON; DECLARE @OrderId int; RETURN 0; END"},
            },
            "RAW_SP",
        ),
        (
            {
                "ok": True,
                "toolName": "get_procedure_definition",
                "data": {
                    "script": (
                        "SET ANSI_NULLS ON\nGO\nSET QUOTED_IDENTIFIER ON\nGO\n"
                        "AS BEGIN SET NOCOUNT ON; RETURN 0; END"
                    )
                },
            },
            "RAW_SP",
        ),
        ({"ok": True, "toolName": "get_procedure_definition", "data": {"definitionText": "AS BEGIN SELECT name FROM dbo.Customer END"}}, "RAW_SP"),
        ({"ok": True, "toolName": "get_procedure_definition", "data": {"routineBody": "BEGIN EXEC dbo.ProcessOrder END"}}, "RAW_SP"),
        ({"ok": True, "toolName": "get_procedure_definition", "data": {"moduleDefinition": "AS BEGIN UPDATE dbo.Customer SET Name = Name END"}}, "RAW_SP"),
        (
            {
                "ok": True,
                "toolName": "search_metadata_objects",
                "diagnostics": "Server=tcp:prod;Database=ERP;Integrated Security=True;",
            },
            "CONNECTION_STRING",
        ),
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


def test_http_error_body_with_connection_string_is_sanitized_before_platform_response():
    body = (
        b'{"error":{"code":"CONNECT_FAILED","message":"login failed for Server=tcp:prod;Database=ERP;'
        b'Integrated Security=True;","details":{"connectionString":"Server=tcp:prod;Database=ERP;"}}}'
    )
    error = urllib.error.HTTPError(
        url="http://mcp.example/tools/search_metadata_objects/invoke",
        code=503,
        msg="Service Unavailable",
        hdrs={},
        fp=BytesIO(body),
    )

    safe_error = MssqlMcpClient()._http_error("/tools/search_metadata_objects/invoke", error)
    response = safe_error.to_response()

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_HTTP_ERROR"
    assert "server=" not in rendered
    assert "connectionstring" not in rendered
    assert "erp" not in rendered
    assert response["error"]["details"] == {
        "path": "/tools/search_metadata_objects/invoke",
        "httpStatus": 503,
    }


def test_external_error_response_with_connection_diagnostics_fails_closed():
    def transport(method, path, payload):
        return {
            "ok": False,
            "error": {
                "code": "CONNECT_FAILED",
                "message": "login failed for mssql+pyodbc://user:pwd@prod-sql/ERP",
                "details": {"connectionString": "Data Source=prod-sql;Initial Catalog=ERP;"},
            },
        }

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(
            "search_metadata_objects",
            {"dbProfileId": "master", "query": "order"},
        )

    assert exc_info.value.code == "MCP_RESPONSE_BLOCKED"
    response = exc_info.value.to_response()
    rendered = str(response).lower()
    assert "mssql+pyodbc" not in rendered
    assert "data source" not in rendered
    assert "prod-sql" not in rendered
    assert "CONNECTION_STRING" in response["error"]["details"]["violations"]


def test_error_to_response_sanitizes_connection_string_diagnostics():
    error = MssqlMcpClientError(
        "MCP_UNAVAILABLE",
        "login failed for Server=tcp:prod;Database=ERP;Integrated Security=True;",
        details={"connectionString": "mssql+pyodbc://user:pwd@prod-sql/ERP"},
    )

    response = error.to_response()

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_UNAVAILABLE"
    assert response["error"]["message"] == "MSSQL MCP error diagnostics were blocked by platform redaction policy."
    assert "server=" not in rendered
    assert "mssql+pyodbc" not in rendered
    assert "prod-sql" not in rendered
    assert response["error"]["details"] == {"violations": ["CONNECTION_STRING"]}


def test_http_error_body_with_jdbc_connection_diagnostic_is_sanitized_before_platform_response():
    body = (
        b'{"error":{"code":"CONNECT_FAILED","message":"login failed for '
        b'jdbc:sqlserver://prod.database.windows.net:1433;databaseName=ERP;encrypt=true;",'
        b'"details":{"diagnostic":"Data Source=prod-sql;Initial Catalog=ERP;Integrated Security=SSPI;"}}}'
    )
    error = urllib.error.HTTPError(
        url="http://mcp.example/tools/search_metadata_objects/invoke",
        code=503,
        msg="Service Unavailable",
        hdrs={},
        fp=BytesIO(body),
    )

    safe_error = MssqlMcpClient()._http_error("/tools/search_metadata_objects/invoke", error)
    response = safe_error.to_response()

    rendered = str(response).lower()
    assert response["error"]["code"] == "MCP_HTTP_ERROR"
    assert "jdbc:sqlserver" not in rendered
    assert "data source" not in rendered
    assert "erp" not in rendered
    assert response["error"]["details"] == {
        "path": "/tools/search_metadata_objects/invoke",
        "httpStatus": 503,
    }
