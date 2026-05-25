# MSSQL MCP / Metadata Gateway

## Objective

Implement read-only metadata tools and blocked operation policy.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G06 Metadata Gateway contract covering the
  external MSSQL MCP REST boundary, runtime tool catalog filtering, allowed
  read-only metadata tools, blocked tool names and payloads, safe response
  envelopes, and metadata search mapping.
- Implement the FastAPI Metadata Gateway client/service/route behavior so
  only allowlisted read-only metadata tools can be exposed or invoked.
- Block row-data, stored procedure execution, free SQL execution, DDL/DML
  apply, source apply, deploy, raw prompt/provider payloads, raw stored
  procedure definitions, and secrets before any external MSSQL MCP transport
  call.
- Fail closed with safe diagnostics when the external MSSQL MCP returns unsafe
  content, non-object JSON, or a mismatched success tool envelope.

## Non-goals

- Do not copy legacy implementation code.
- Do not weaken blocked-operation policy.
- Do not merge Development Codex and Service Codex Runner realms.

## Constraints

- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Validation gate controls artifact persistence.
- No row data, SP execution, DDL/DML apply, source apply, deploy, raw prompt/provider storage.

## Files to create or modify

See the phase plan in `docs/release/v2-implementation-plan.md` after G12, or the root `README.md` for the phase list.

Expected G06 files include:

- `spec/development/mssql_mcp_metadata_gateway.yaml`
- `spec/mcp/mssql_metadata_tool_catalog.yaml`
- `spec/eval/v2_mssql_mcp_readonly.yaml`
- `apps/api/api_app/services/mssql_mcp_client.py`
- `apps/api/api_app/services/metadata_service.py`
- `apps/api/api_app/routes/metadata.py`
- focused contract/unit/integration/security/eval tests for the G06 metadata
  gateway policy

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- The runtime metadata tool catalog returned by the platform includes only
  allowlisted tools that explicitly declare `readOnly: true`; blocked,
  mutation, execution, and unknown tools are filtered out.
- Metadata tool invocation blocks unsafe or unknown tool names and unsafe
  arguments before the external transport is called.
- Metadata search maps only to `search_metadata_objects`, enforces query and
  limit boundaries, and blocks unsafe search payloads before proxying.
- External MCP success responses must name the requested allowlisted tool and
  must not contain row data, secrets, raw prompts, raw provider responses, raw
  stored procedure definitions, or executable/apply instructions.
- Metadata Gateway safe errors do not include SQL text, connection strings,
  credentials, row data, stored procedure execution output, raw prompts, or raw
  provider responses.

## Validation commands

```bash
python -m pytest tests/contract/test_g06_mssql_mcp_metadata_gateway.py tests/unit/api/test_mssql_mcp_client.py tests/unit/api/test_g06_mssql_mcp_client_policy.py tests/integration/test_metadata_routes.py tests/integration/test_g06_metadata_gateway_routes.py tests/security/test_forbidden_operations.py tests/security/test_g06_mssql_mcp_policy.py tests/eval/test_g06_mssql_mcp_readonly_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
