from apps.api.api_app.services.mssql_mcp_client import (
    MssqlMcpClient,
    MssqlMcpClientError,
    is_blocked_mcp_tool_name,
)
from plf_agent_validation.redaction_validator import find_redaction_violations


def test_mssql_mcp_blocks_forbidden_tools():
    for tool in ["execute_sql", "execute_procedure", "query_row_data", "apply_ddl", "apply_dml", "deploy_source"]:
        assert is_blocked_mcp_tool_name(tool)


def test_external_mssql_mcp_allows_metadata_tool_names():
    for tool in ["search_metadata_objects", "get_table_schema", "get_procedure_definition", "get_procedure_dependencies"]:
        assert not is_blocked_mcp_tool_name(tool)


def test_blocked_tool_does_not_reach_external_transport():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    client = MssqlMcpClient(transport=transport)
    try:
        client.invoke_tool("execute_sql", {"dbProfileId": "master"})
    except MssqlMcpClientError as exc:
        assert exc.code == "MCP_TOOL_BLOCKED"
    else:  # pragma: no cover
        raise AssertionError("blocked tool should raise")
    assert calls == []


def test_redaction_detects_raw_payloads():
    assert "RAW_PROMPT" in find_redaction_violations("raw prompt: hello")
    assert "SECRET" in find_redaction_violations("password=abc")
    assert "ROW_DATA" in find_redaction_violations("select * from users")
