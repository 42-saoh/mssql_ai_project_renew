from __future__ import annotations

from typing import Any

from .mssql_mcp_client import MssqlMcpClientError, get_mssql_mcp_client


def _safe_call(callback) -> dict[str, Any]:
    try:
        return callback()
    except MssqlMcpClientError as exc:
        return exc.to_response()


def metadata_ready() -> dict[str, Any]:
    return _safe_call(lambda: get_mssql_mcp_client().ready())


def list_metadata_tools() -> dict[str, Any]:
    return _safe_call(lambda: get_mssql_mcp_client().list_tools())


def list_db_profiles() -> dict[str, Any]:
    return _safe_call(lambda: get_mssql_mcp_client().list_db_profiles())


def invoke_metadata_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return _safe_call(lambda: get_mssql_mcp_client().invoke_tool(tool_name, arguments or {}))


def search_metadata(
    query: str,
    *,
    db_profile_id: str = "master",
    object_types: list[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    return _safe_call(
        lambda: get_mssql_mcp_client().search_metadata(
            query,
            db_profile_id=db_profile_id,
            object_types=object_types,
            limit=limit,
        )
    )
