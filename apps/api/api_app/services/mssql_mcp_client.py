from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from plf_agent_validation.redaction_validator import find_redaction_violations

DEFAULT_METADATA_GATEWAY_URL = "http://localhost:8100"

BLOCKED_MCP_TOOL_NAMES = {
    "execute_sql",
    "execute_procedure",
    "query_row_data",
    "apply_ddl",
    "apply_dml",
    "deploy_source",
}

_BLOCKED_TOOL_PREFIXES = ("execute_", "apply_", "deploy_")
_BLOCKED_TOOL_FRAGMENTS = ("row_data", "free_sql", "ddl_apply", "dml_apply")
_TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

Transport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


@dataclass(frozen=True)
class MssqlMcpClientError(Exception):
    code: str
    message: str
    status_code: int = 502
    details: dict[str, Any] = field(default_factory=dict)

    def to_response(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }
        if self.details:
            payload["error"]["details"] = self.details
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


def _safe_payload_violations(payload: Any) -> list[str]:
    text = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
    return find_redaction_violations(text)


@dataclass(frozen=True)
class MssqlMcpClient:
    base_url: str = DEFAULT_METADATA_GATEWAY_URL
    timeout_seconds: int = 10
    transport: Transport | None = None

    def ready(self) -> dict[str, Any]:
        return self._request_json("GET", "/health/ready")

    def list_tools(self) -> dict[str, Any]:
        return self._request_json("GET", "/catalog/tools")

    def list_db_profiles(self) -> dict[str, Any]:
        return self._request_json("GET", "/config/db-profiles")

    def invoke_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        self._assert_invocation_allowed(tool_name, arguments or {})
        return self._request_json(
            "POST",
            f"/tools/{tool_name}/invoke",
            {"arguments": arguments or {}},
        )

    def search_metadata(
        self,
        query: str,
        *,
        db_profile_id: str = "master",
        object_types: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "dbProfileId": db_profile_id,
            "query": query,
            "limit": limit,
        }
        if object_types:
            arguments["objectTypes"] = object_types
        return self.invoke_tool("search_metadata_objects", arguments)

    def _assert_invocation_allowed(self, tool_name: str, arguments: dict[str, Any]) -> None:
        if is_blocked_mcp_tool_name(tool_name):
            raise MssqlMcpClientError(
                "MCP_TOOL_BLOCKED",
                "Requested MCP tool is blocked by platform read-only policy.",
                status_code=403,
                details={"toolName": tool_name},
            )
        violations = _safe_payload_violations(arguments)
        if violations:
            raise MssqlMcpClientError(
                "MCP_ARGUMENTS_BLOCKED",
                "MCP arguments contain content blocked by platform redaction policy.",
                status_code=400,
                details={"violations": violations},
            )

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(method, path, payload)

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
        if not isinstance(parsed, dict):
            raise MssqlMcpClientError(
                "MCP_INVALID_RESPONSE",
                "External MSSQL MCP response must be a JSON object.",
                details={"path": path},
            )
        return parsed

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
        details = {**details, "path": path, "httpStatus": exc.code}
        return MssqlMcpClientError(code, message, status_code=exc.code, details=details)

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"


def get_mssql_mcp_client() -> MssqlMcpClient:
    return MssqlMcpClient(
        base_url=os.getenv("PLF_METADATA_GATEWAY_URL", DEFAULT_METADATA_GATEWAY_URL),
    )
