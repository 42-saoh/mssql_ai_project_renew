# V2 Acceptance Report

## G12 Final Acceptance

This report records local G12 release acceptance for PLF DB Agent V2. The
accepted scope is the greenfield repository implementation and its local
contract, unit, integration, security, eval, and E2E gates. It is not a
production deployment approval.

## Acceptance Scenario Matrix

| Scenario | Expected result | Evidence |
|---|---|---|
| Runner-backed analysis request | Chat routes to Service Codex Runner metadata, records proposal-only codex run metadata, and persists no artifact content before validation. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Validation-gated artifact persistence | A validated proposal persists only draft/manual-review artifact metadata with `productionReady=false`, `reviewRequired=true`, review markers, content reference, and content hash. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Metadata search | Chat calls the Metadata Gateway search service and does not create runner submissions, approvals, or artifacts. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Sanitized history lookup | History returns prior run summaries without raw user messages, raw prompts, provider responses, row data, raw stored procedure definitions, or secrets. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Approval review | DDL/DML apply requests create policy-review metadata only; approval resume has no DB execution, runner submission, artifact persistence, source apply, or deploy side effects. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Stored procedure execution block | Stored procedure execution requests hard-block before PGPT, Metadata Gateway, runner submission, approval side effects, or artifact persistence. | `tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py` |
| Release report publication | Acceptance, security, eval, runbook, and known limitations reports are concrete, non-placeholder release artifacts. | `tests/contract/test_g12_end_to_end_acceptance_release.py` |

## Preserved Policy Boundaries

- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Validation gate controls artifact persistence.
- No row data.
- No stored procedure execution.
- No free SQL execution.
- No DDL/DML apply.
- No source apply.
- No deploy.
- No raw prompt persistence.
- No raw provider response persistence.
- No raw stored procedure definition persistence.
- No secret persistence.

## Validation Commands

```bash
python -m pytest tests/contract/test_g12_end_to_end_acceptance_release.py tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py tests/eval/test_g12_end_to_end_acceptance_release_eval.py -q
make test
```

The full release gate also includes the suites listed in `EVAL_SPEC.md`:
`make test-contract`, `make test-unit`, `make test-integration`,
`make test-security`, `make test-eval`, and `make test-e2e`.

## Published Reports

- Security: `docs/release/v2-security-report.md`
- Eval: `docs/release/v2-eval-report.md`
- Runbook: `docs/release/v2-runbook.md`
- Known limitations: `docs/release/v2-known-limitations.md`

## Release Decision

V2 is accepted for local greenfield release validation when the G12 focused
tests and `make test` pass with the policy boundaries above intact. Production
deployment, customer MSSQL connectivity, and real external runner operations
remain outside this release decision.
