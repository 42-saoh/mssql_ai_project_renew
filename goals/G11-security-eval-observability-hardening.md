# Security / Eval / Observability Hardening

## Objective

Harden cross-realm boundary, storage redaction, forbidden operations, observability, and runbooks.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G11 security/eval/observability hardening contract
  that maps policy boundaries, storage redaction controls, safe observability
  events, eval hardening cases, and release runbook files.
- Add sanitized observability event persistence for chat, runner submission,
  artifact validation/persistence, and approval review transitions without
  storing raw prompts, raw provider responses, raw stored procedure
  definitions, row data, secrets, connection strings, source content, runner
  stdout, or runner stderr.
- Update release security, eval, and runbook documents with G11 hardening
  validation steps and incident response for redaction findings.

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

Expected G11 files include:

- `spec/development/security_eval_observability_hardening.yaml`
- `apps/api/api_app/services/observability_service.py`
- `apps/api/api_app/repositories/observability_repository.py`
- `spec/eval/v2_storage_redaction.yaml`
- `spec/eval/v2_blocked_request_paths.yaml`
- `docs/release/v2-security-report.md`
- `docs/release/v2-eval-report.md`
- `docs/release/v2-runbook.md`
- focused contract/security/eval tests for G11 hardening

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Observability event persistence uses an allowlist of safe metadata fields,
  sanitizes redaction blocker codes, and rejects unsupported or unsafe fields
  before repository writes.
- Chat runs, runner submissions, artifact validation/persistence, and approval
  resume transitions emit only sanitized observability metadata.
- Blocked stored-procedure execution, raw-payload, row-data, secret, and
  connection-string paths still hard-block before metadata gateway proxying,
  runner submission, artifact persistence, approval resume side effects, DB
  execution, source apply, or deploy.
- Release security, eval, and runbook documents describe policy boundaries,
  storage redaction, safe observability, validation commands, and redaction
  incident response.

## Validation commands

```bash
python -m pytest tests/contract/test_g11_security_eval_observability_hardening.py tests/security/test_g11_observability_storage_hardening.py tests/eval/test_g11_security_eval_observability_hardening_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
