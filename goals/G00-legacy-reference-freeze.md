# Legacy Reference Freeze

## Objective

Freeze the legacy project as reference-only material and document what V2 inherits as policy, taxonomy, and eval lessons.

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
- If a root `.env` is found during G00 execution, quarantine it without reading,
  printing, committing, or copying its contents. Move it to an ignored location
  outside the repository, then verify `.env.example` remains the only
  environment contract in the Development Codex workspace.

## Files to create or modify

See the phase plan in `docs/release/v2-implementation-plan.md` after G12, or the root `README.md` for the phase list.

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Root `.env` is not persisted in the Development Codex workspace; `.env.example`
  remains the only repository environment contract and must keep secret values
  blank or placeholder-only.
- Stored procedure execution requests, including run/call/exec procedure forms
  in English and Korean, including Korean object-particle forms, hard-block
  before metadata gateway, runner submission, artifact persistence, or approval
  side effects.

## Validation commands

```powershell
if (Test-Path -LiteralPath .env) { throw "root .env must not exist" }
python -m pytest tests/security/test_g00_legacy_freeze_boundary.py::test_root_env_file_is_not_persisted_as_development_contract -q
```

```bash
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
