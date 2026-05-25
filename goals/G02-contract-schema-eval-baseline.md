# Contract / Schema / Eval Baseline

## Objective

Define OpenAPI, runner schemas, artifact schemas, DB schema, and eval baseline before implementation.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.

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

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Unsafe artifact review markers that contain raw prompt, raw provider
  response, or secret markers must be blocked before artifact persistence;
  API responses must report `RAW_PROMPT`, `RAW_PROVIDER_RESPONSE`, and
  `SECRET` blocker codes while persisted validation records keep only
  sanitized blocker codes and empty review markers.

## Validation commands

```bash
python -m pytest tests/security/test_g02_schema_security.py::test_blocked_artifact_review_markers_are_not_persisted_raw -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
