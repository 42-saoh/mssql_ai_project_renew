# End-to-End Acceptance & V2 Release

## Objective

Run final acceptance scenarios and publish release, security, eval, runbook, and known limitations reports.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G12 release contract that maps final acceptance
  scenarios, published release reports, required validation gates, known
  limitations, and preserved policy boundaries.
- Publish final acceptance, security, eval, runbook, and known limitations
  reports with concrete validation commands and release-scope limitations.
- Extend the `v2_end_to_end_happy_paths` eval suite with local final
  acceptance cases for runner-backed proposal flow, metadata search, sanitized
  history, validation-gated artifact persistence, approval review, and hard
  blocked request paths while preserving the G02 baseline suite contract.

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

Expected G12 files include:

- `spec/development/end_to_end_acceptance_release.yaml`
- `spec/eval/v2_end_to_end_happy_paths.yaml`
- `docs/release/v2-acceptance-report.md`
- `docs/release/v2-security-report.md`
- `docs/release/v2-eval-report.md`
- `docs/release/v2-runbook.md`
- `docs/release/v2-known-limitations.md`
- focused contract/e2e/eval tests for G12 release acceptance

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- G12 release contract and final release reports are not placeholders and
  explicitly preserve Streamlit FastAPI-only, Service Codex Runner
  proposal-only, validation-gated persistence, no row data, no stored
  procedure execution, no DDL/DML apply, no source apply, no deploy, and no raw
  prompt/provider/secret persistence boundaries.
- Final acceptance scenarios cover runner-backed proposal metadata,
  metadata-search response handling, sanitized history lookup, validation-gated
  artifact persistence, approval resume without side effects, and hard blocked
  stored-procedure execution.
- `v2_end_to_end_happy_paths` preserves the G02 baseline case and references
  concrete G12 local test evidence.
- Known limitations clearly distinguish local greenfield release acceptance
  from production deployment, production MSSQL connectivity, real external
  Service Codex execution, and optional browser smoke checks.

## Validation commands

```bash
python -m pytest tests/contract/test_g12_end_to_end_acceptance_release.py tests/e2e/test_g12_end_to_end_acceptance_release_e2e.py tests/eval/test_g12_end_to_end_acceptance_release_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
