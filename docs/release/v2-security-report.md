# V2 Security Report

## Scope

This G11 hardening report covers the Development Codex Realm and the Service
Codex Runner Realm before G12 release acceptance. It is a regression contract
for the policy boundaries already established in G00 through G10.

## Enforced Boundaries

- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Runtime workspaces are copied only from
  `services/codex-runner/runtime-template`.
- Validation gates control artifact persistence.
- Row data, stored procedure execution, free SQL execution, DDL/DML apply,
  source apply, deploy, raw prompt persistence, raw provider response
  persistence, raw stored procedure definitions, and secrets remain forbidden.

## Storage Redaction

All platform persistence paths must pass sanitized payloads through
`apps/api/api_app/services/persistence_safety.py` and the shared redaction
validator before repository writes. Unsafe marker codes include `RAW_PROMPT`,
`RAW_PROVIDER_RESPONSE`, `RAW_SP`, `ROW_DATA`, `SECRET`, and
`CONNECTION_STRING`.

Blocked artifact validation records may keep only safe blocker codes and empty
review markers when unsafe payloads are detected. Observability events may keep
only safe metadata fields and sanitized blocker codes.

## Observability Policy

LangSmith tracing is development-only and disabled by default. It requires
`PLF_ENVIRONMENT=dev`, `PLF_LANGSMITH_ENABLED=true`,
`LANGSMITH_TRACING=true`, and a present `LANGSMITH_API_KEY`.

Persisted observability events are local platform metadata only. They must not
store raw prompts, raw provider responses, raw stored procedure definitions,
row data, secrets, connection strings, runner stdout, runner stderr, or source
content.

## Incident Response

If a redaction finding occurs:

1. Treat the request or artifact as blocked.
2. Persist only sanitized blocker codes and safe event metadata.
3. Confirm no artifact, approval resume, runner submission, DB execution,
   source apply, or deploy side effect occurred unless that side effect is
   explicitly allowed by the active policy contract.
4. Run the focused G11 security and eval tests before resuming release work.

## G12 Release Security Position

G12 release acceptance does not add policy exceptions. The final acceptance
suite must preserve Streamlit calls FastAPI only, Service Codex Runner returns
proposals only, validation gate controls artifact persistence, no row data, no
stored procedure execution, no free SQL execution, no DDL/DML apply, no source
apply, no deploy, no raw prompt persistence, no raw provider response
persistence, no raw stored procedure definition persistence, and no secret
persistence.

Security validation for release:

```bash
python -m pytest tests/contract/test_g12_end_to_end_acceptance_release.py tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py tests/eval/test_g12_end_to_end_acceptance_release_eval.py -q
make test
```
