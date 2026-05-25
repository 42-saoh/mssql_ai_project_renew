from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from plf_agent_orchestration.forbidden_operations import detect_forbidden_operation_blockers
from plf_agent_validation.redaction_validator import find_redaction_violations

DEFAULT_METADATA_GATEWAY_URL = "http://localhost:8100"

ALLOWED_METADATA_TOOL_NAMES = {
    "search_metadata_objects",
    "describe_object",
    "find_references",
    "get_table_schema",
    "get_table_columns",
    "get_table_indexes",
    "get_table_relationships",
    "get_object_dependencies",
    "get_procedure_metadata",
    "get_procedure_definition",
    "get_procedure_dependencies",
}

BLOCKED_MCP_TOOL_NAMES = {
    "execute_sql",
    "execute_procedure",
    "query_row_data",
    "apply_ddl",
    "apply_dml",
    "deploy_source",
    "create_object",
    "alter_object",
    "drop_object",
    "truncate_table",
    "insert_row",
    "update_row",
    "delete_row",
    "merge_rows",
    "backup_database",
    "restore_database",
    "grant_permission",
    "revoke_permission",
}

_BLOCKED_TOOL_PREFIXES = (
    "execute_",
    "apply_",
    "deploy_",
    "create_",
    "alter_",
    "drop_",
    "truncate_",
    "insert_",
    "update_",
    "delete_",
    "merge_",
    "backup_",
    "restore_",
    "grant_",
    "revoke_",
)
_BLOCKED_TOOL_FRAGMENTS = (
    "row_data",
    "free_sql",
    "ddl_apply",
    "dml_apply",
    "procedure_execution",
    "source_apply",
)
_TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_DB_PROFILE_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_MCP_PAYLOAD_BLOCKED_PATTERNS = {
    "SQL_EXECUTION": re.compile(r"\b(?:exec|execute)\b", re.I),
    "DDL_DML_APPLY": re.compile(
        r"\b(?:insert|update|delete|merge|truncate|create|alter|drop|grant|revoke)\b",
        re.I,
    ),
    "SOURCE_APPLY_OR_DEPLOY": re.compile(r"\b(?:deploy|apply\s+source|overwrite\s+source)\b", re.I),
}
_MCP_FORBIDDEN_OPERATION_CODES = {
    "STORED_PROCEDURE_EXECUTION_BLOCKED",
}
_MIN_METADATA_LIMIT = 1
_MAX_METADATA_LIMIT = 100

Transport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


@dataclass(frozen=True)
class MssqlMcpClientError(Exception):
    code: str
    message: str
    status_code: int = 502
    details: dict[str, Any] = field(default_factory=dict)

    def to_response(self) -> dict[str, Any]:
        code = self.code
        message = self.message
        details = self.details
        violations = _safe_payload_violations({"code": code, "message": message, "details": details})
        if violations:
            code = code if str(code).startswith("MCP_") else "MCP_ERROR"
            message = "MSSQL MCP error diagnostics were blocked by platform redaction policy."
            details = {"violations": sorted(set(violations))}

        payload: dict[str, Any] = {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
        if details:
            payload["error"]["details"] = details
        return payload


def normalize_tool_name(tool_name: str) -> str:
    return (tool_name or "").strip().lower().replace("-", "_")


def is_blocked_mcp_tool_name(tool_name: str) -> bool:
    normalized = normalize_tool_name(tool_name)
    if not normalized:
        return True
    if _TOOL_NAME_PATTERN.fullmatch(tool_name.strip() or "") is None:
        return True
    if normalized in BLOCKED_MCP_TOOL_NAMES:
        return True
    if normalized.startswith(_BLOCKED_TOOL_PREFIXES):
        return True
    return any(fragment in normalized for fragment in _BLOCKED_TOOL_FRAGMENTS)


def is_allowed_metadata_tool_name(tool_name: str) -> bool:
    normalized = normalize_tool_name(tool_name)
    return not is_blocked_mcp_tool_name(tool_name) and normalized in ALLOWED_METADATA_TOOL_NAMES


def _safe_payload_violations(payload: Any) -> list[str]:
    text = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
    violations = list(find_redaction_violations(text))
    for code, pattern in _MCP_PAYLOAD_BLOCKED_PATTERNS.items():
        if pattern.search(text) and code not in violations:
            violations.append(code)
    for code in detect_forbidden_operation_blockers(text):
        if code in _MCP_FORBIDDEN_OPERATION_CODES and code not in violations:
            violations.append(code)
    return violations


def _safe_tool_name_for_diagnostics(tool_name: str) -> str:
    stripped = (tool_name or "").strip()
    if _safe_payload_violations({"toolName": stripped}):
        return "<redacted>"
    if _TOOL_NAME_PATTERN.fullmatch(stripped) is None:
        return "<invalid>"
    return normalize_tool_name(stripped)


@dataclass(frozen=True)
class MssqlMcpClient:
    base_url: str = DEFAULT_METADATA_GATEWAY_URL
    timeout_seconds: int = 10
    transport: Transport | None = None

    def ready(self) -> dict[str, Any]:
        return self._request_json("GET", "/health/ready")

    def list_tools(self) -> dict[str, Any]:
        return _filter_tool_catalog(self._request_json("GET", "/catalog/tools"))

    def list_db_profiles(self) -> dict[str, Any]:
        return self._request_json("GET", "/config/db-profiles")

    def invoke_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        self._assert_invocation_allowed(tool_name, arguments or {})
        response = self._request_json(
            "POST",
            f"/tools/{tool_name}/invoke",
            {"arguments": arguments or {}},
        )
        return self._validate_tool_response(tool_name, response)

    def search_metadata(
        self,
        query: str,
        *,
        db_profile_id: str = "master",
        object_types: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = _metadata_search_arguments(
            query,
            db_profile_id=db_profile_id,
            limit=limit,
        )
        if object_types:
            arguments["objectTypes"] = object_types
        return self.invoke_tool("search_metadata_objects", arguments)

    def _assert_invocation_allowed(self, tool_name: str, arguments: dict[str, Any]) -> None:
        if not is_allowed_metadata_tool_name(tool_name):
            raise MssqlMcpClientError(
                "MCP_TOOL_BLOCKED",
                "Requested MCP tool is blocked by platform read-only policy.",
                status_code=403,
                details={
                    "toolName": _safe_tool_name_for_diagnostics(tool_name),
                    "readOnlyMetadataTool": False,
                },
            )
        violations = _safe_payload_violations(arguments)
        if violations:
            raise MssqlMcpClientError(
                "MCP_ARGUMENTS_BLOCKED",
                "MCP arguments contain content blocked by platform redaction policy.",
                status_code=400,
                details={"violations": violations},
            )

    def _validate_tool_response(self, requested_tool_name: str, response: dict[str, Any]) -> dict[str, Any]:
        if response.get("ok") is False:
            return response
        response_tool_name = response.get("toolName")
        if not isinstance(response_tool_name, str):
            raise MssqlMcpClientError(
                "MCP_INVALID_RESPONSE",
                "External MSSQL MCP success response must include a toolName.",
                details={"toolName": requested_tool_name},
            )
        if normalize_tool_name(response_tool_name) != normalize_tool_name(requested_tool_name):
            raise MssqlMcpClientError(
                "MCP_INVALID_RESPONSE",
                "External MSSQL MCP response toolName did not match the requested tool.",
                details={"toolName": requested_tool_name, "responseToolName": response_tool_name},
            )
        if not is_allowed_metadata_tool_name(response_tool_name):
            raise MssqlMcpClientError(
                "MCP_RESPONSE_BLOCKED",
                "External MSSQL MCP response referenced a blocked tool.",
                details={"toolName": response_tool_name},
            )
        return response

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.transport is not None:
            return self._validate_response_payload(path, self.transport(method, path, payload))

        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self._url(path),
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise self._http_error(path, exc) from exc
        except urllib.error.URLError as exc:
            raise MssqlMcpClientError(
                "MCP_UNAVAILABLE",
                "External MSSQL MCP is unavailable.",
                details={
                    "path": path,
                    "timeoutSeconds": self.timeout_seconds,
                    "errorClass": exc.__class__.__name__,
                },
            ) from exc

        if not body:
            return {}
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise MssqlMcpClientError(
                "MCP_INVALID_RESPONSE",
                "External MSSQL MCP returned invalid JSON.",
                details={"path": path, "errorClass": exc.__class__.__name__},
            ) from exc
        return self._validate_response_payload(path, parsed)

    def _http_error(self, path: str, exc: urllib.error.HTTPError) -> MssqlMcpClientError:
        try:
            body = exc.read().decode("utf-8")
            parsed = json.loads(body) if body else {}
        except Exception:
            parsed = {}
        safe_error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(safe_error, dict):
            message = str(safe_error.get("message") or "External MSSQL MCP rejected the request.")
            code = str(safe_error.get("code") or "MCP_HTTP_ERROR")
            details = safe_error.get("details") if isinstance(safe_error.get("details"), dict) else {}
        else:
            message = "External MSSQL MCP rejected the request."
            code = "MCP_HTTP_ERROR"
            details = {}
        if _safe_payload_violations({"code": code, "message": message, "details": details}):
            code = "MCP_HTTP_ERROR"
            message = "External MSSQL MCP rejected the request."
            details = {}
        details = {**details, "path": path, "httpStatus": exc.code}
        return MssqlMcpClientError(code, message, status_code=exc.code, details=details)

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _validate_response_payload(self, path: str, parsed: Any) -> dict[str, Any]:
        if not isinstance(parsed, dict):
            raise MssqlMcpClientError(
                "MCP_INVALID_RESPONSE",
                "External MSSQL MCP response must be a JSON object.",
                details={"path": path},
            )
        violations = _safe_payload_violations(parsed)
        if violations:
            raise MssqlMcpClientError(
                "MCP_RESPONSE_BLOCKED",
                "External MSSQL MCP response contained content blocked by platform read-only policy.",
                details={"path": path, "violations": violations},
            )
        return parsed


def get_mssql_mcp_client() -> MssqlMcpClient:
    return MssqlMcpClient(
        base_url=os.getenv("PLF_METADATA_GATEWAY_URL", DEFAULT_METADATA_GATEWAY_URL),
    )


def _metadata_search_arguments(query: str, *, db_profile_id: str, limit: int) -> dict[str, Any]:
    normalized_query = (query or "").strip()
    if not normalized_query:
        raise MssqlMcpClientError(
            "MCP_ARGUMENTS_BLOCKED",
            "Metadata search query must not be empty.",
            status_code=400,
            details={"field": "query"},
        )
    if not _DB_PROFILE_PATTERN.fullmatch(db_profile_id or ""):
        raise MssqlMcpClientError(
            "MCP_ARGUMENTS_BLOCKED",
            "Metadata dbProfileId is not allowed.",
            status_code=400,
            details={"field": "dbProfileId"},
        )
    if limit < _MIN_METADATA_LIMIT or limit > _MAX_METADATA_LIMIT:
        raise MssqlMcpClientError(
            "MCP_ARGUMENTS_BLOCKED",
            "Metadata search limit is outside the allowed range.",
            status_code=400,
            details={"field": "limit", "minimum": _MIN_METADATA_LIMIT, "maximum": _MAX_METADATA_LIMIT},
        )
    return {
        "dbProfileId": db_profile_id,
        "query": normalized_query,
        "limit": limit,
    }


def _filter_tool_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    tools = catalog.get("tools")
    if not isinstance(tools, list):
        raise MssqlMcpClientError(
            "MCP_INVALID_RESPONSE",
            "External MSSQL MCP catalog must include a tools list.",
            details={"field": "tools"},
        )

    filtered: list[dict[str, Any]] = []
    rejected_count = 0
    for tool in tools:
        if not isinstance(tool, dict):
            rejected_count += 1
            continue
        name = str(tool.get("name") or "")
        if tool.get("readOnly") is not True or not is_allowed_metadata_tool_name(name):
            rejected_count += 1
            continue
        filtered_tool = dict(tool)
        filtered_tool["name"] = normalize_tool_name(name)
        filtered_tool["readOnly"] = True
        filtered.append(filtered_tool)

    result = dict(catalog)
    result["tools"] = filtered
    result["policy"] = {
        "readOnlyMetadataOnly": True,
        "allowedToolNames": sorted(ALLOWED_METADATA_TOOL_NAMES),
        "filteredToolCount": rejected_count,
    }
    return result
