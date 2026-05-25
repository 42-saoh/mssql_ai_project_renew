# Eval Specification

## Required gates

- `make test-contract`
- `make test-unit`
- `make test-integration`
- `make test-security`
- `make test-eval`
- `make test-e2e`

## Eval suites

- `v2_cross_realm_boundary`
- `v2_domain_guard`
- `v2_intent_routing`
- `v2_runner_policy`
- `v2_runner_output_schema`
- `v2_storage_redaction`
- `v2_artifact_quality`
- `v2_artifact_history_approval_ux`
- `v2_mssql_mcp_readonly`
- `v2_streamlit_api_only`
- `v2_end_to_end_happy_paths`
- `v2_blocked_request_paths`

## Hard fail conditions

- Service Codex Runner uses root development skills.
- Streamlit directly accesses DB/MCP/Runner.
- Raw prompt, raw provider response, raw SP, row data, or secrets are persisted.
- DDL/DML/SP execution is allowed.
- General chatbot request is answered.
