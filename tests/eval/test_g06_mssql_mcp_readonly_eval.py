from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from apps.api.api_app.services.mssql_mcp_client import MssqlMcpClient, MssqlMcpClientError

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_g06_mssql_mcp_readonly_eval_cases_are_declared():
    eval_spec = _load_yaml("spec/eval/v2_mssql_mcp_readonly.yaml")
    case_ids = {case["id"] for case in eval_spec["cases"]}

    assert "g06_metadata_gateway_filters_runtime_catalog_to_readonly_allowlist" in case_ids
    assert "g06_blocked_mcp_tools_and_unsafe_payloads_do_not_reach_transport" in case_ids
    assert "g06_unsafe_mcp_responses_fail_closed" in case_ids


def test_g06_eval_catalog_filters_blocked_and_unknown_tools():
    def transport(method, path, payload):
        return {
            "tools": [
                {"name": "search_metadata_objects", "readOnly": True},
                {"name": "execute_sql", "readOnly": False},
                {"name": "unknown_readonly_tool", "readOnly": True},
            ]
        }

    catalog = MssqlMcpClient(transport=transport).list_tools()

    assert [tool["name"] for tool in catalog["tools"]] == ["search_metadata_objects"]


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("execute_sql", {"dbProfileId": "master", "sql": "select * from users"}),
        ("apply_ddl", {"dbProfileId": "master", "ddl": "drop table dbo.X"}),
        ("unknown_readonly_tool", {"dbProfileId": "master", "query": "order"}),
        ("search_metadata_objects", {"dbProfileId": "master", "query": "raw provider response: abc"}),
    ],
)
def test_g06_eval_blocked_requests_do_not_reach_transport(tool_name, arguments):
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"ok": True}

    with pytest.raises(MssqlMcpClientError):
        MssqlMcpClient(transport=transport).invoke_tool(tool_name, arguments)

    assert calls == []


def test_g06_eval_unsafe_response_fails_closed():
    def transport(method, path, payload):
        return {
            "ok": True,
            "toolName": "search_metadata_objects",
            "data": {"definition": "create procedure dbo.X as select 1"},
        }

    with pytest.raises(MssqlMcpClientError) as exc_info:
        MssqlMcpClient(transport=transport).invoke_tool(
            "search_metadata_objects",
            {"dbProfileId": "master", "query": "procedure X"},
        )

    assert exc_info.value.code == "MCP_RESPONSE_BLOCKED"
    assert "RAW_SP" in exc_info.value.details["violations"]
