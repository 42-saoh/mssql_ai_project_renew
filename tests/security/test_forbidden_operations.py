import pytest

from apps.api.api_app.repositories import (
    approval_repository,
    artifact_repository,
    conversation_repository,
    run_repository,
    validation_repository,
)
from apps.api.api_app.services import chat_service
from apps.api.api_app.services.mssql_mcp_client import (
    MssqlMcpClient,
    MssqlMcpClientError,
    is_blocked_mcp_tool_name,
)
from plf_agent_validation.redaction_validator import find_redaction_violations


def _clear_repositories():
    conversation_repository.clear()
    run_repository.clear()
    artifact_repository.clear()
    validation_repository.clear()
    approval_repository.clear()


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
    assert "CONNECTION_STRING" in find_redaction_violations(
        "Server=tcp:prod;Database=ERP;Integrated Security=True;"
    )
    assert "RAW_SP" in find_redaction_violations('{"procedureDefinition":"AS BEGIN SELECT 1 END"}')


@pytest.mark.parametrize(
    "payload",
    [
        "select name from dbo.Customer",
        '{"data":{"rows":[{"customer":"alice"}]}}',
        '{"data":{"records":[{"customer":"alice"}]}}',
        '{"data":{"values":["alice"]}}',
        '{"resultSet":[{"customer":"alice"}]}',
        "\uc0d8\ud50c \ub370\uc774\ud130\ub97c \ubcf4\uc5ec\uc918",
    ],
)
def test_redaction_detects_free_sql_and_structured_row_data(payload):
    assert "ROW_DATA" in find_redaction_violations(payload)


@pytest.mark.parametrize(
    "message",
    [
        "exec dbo.ProcessOrder",
        "\uc800\uc7a5 \ud504\ub85c\uc2dc\uc800\ub97c \ud638\ucd9c\ud574\uc918",
        "\ud504\ub85c\uc2dc\uc800\ub97c \uc2e4\ud589\ud574\uc918",
        "SP\ub97c \uc2e4\ud589\ud574\uc918",
    ],
)
def test_stored_procedure_execution_request_has_no_downstream_side_effects(message):
    _clear_repositories()

    response = chat_service.create_chat_run(message, actor_id="analyst-1")

    assert response["status"] == "BLOCKED"
    assert response["policyDecision"] == "BLOCKED"
    assert response["route"] == "blocked"
    assert "STORED_PROCEDURE_EXECUTION_BLOCKED" in response["blockers"]
    assert "approvalId" not in response
    assert "codexRunId" not in response
    assert approval_repository.list_all() == []
    assert run_repository.list_codex_runs() == []
    assert artifact_repository.list_all() == []
