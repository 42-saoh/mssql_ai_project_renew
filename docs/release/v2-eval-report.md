# V2 Eval Report

## G11 Eval Hardening

G11 strengthens the release eval surface for security, storage redaction, and
safe observability. The release gate continues to include the suites listed in
`EVAL_SPEC.md`, with focused G11 coverage added to:

- `v2_storage_redaction`
- `v2_blocked_request_paths`
- `v2_cross_realm_boundary`
- `v2_runner_policy`
- `v2_mssql_mcp_readonly`
- `v2_streamlit_api_only`

## Added G11 Cases

- `g11_observability_events_store_safe_codes_only`
- `g11_release_runbooks_document_redaction_response`
- `g11_blocked_requests_emit_safe_observability_without_side_effects`

## Validation Commands

```bash
python -m pytest tests/contract/test_g11_security_eval_observability_hardening.py tests/security/test_g11_observability_storage_hardening.py tests/eval/test_g11_security_eval_observability_hardening_eval.py -q
make test
```

## Hard Fail Coverage

The eval suite remains a hard fail if any path allows root development skills
in the runtime realm, direct Streamlit DB/MCP/Runner access, raw prompt or
provider persistence, raw stored procedure definitions, row data, secrets,
DDL/DML/SP execution, source apply, deploy, or general chatbot answers.
