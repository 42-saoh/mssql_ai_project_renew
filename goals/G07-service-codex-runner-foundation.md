# Service Codex Runner Foundation

## Objective

Implement isolated workspace creation, runtime-template copy, codex exec wrapper, event parsing, and validation.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G07 Service Codex Runner foundation contract
  covering isolated workspace creation, runtime-template-only copies, run input
  materialization, `codex exec` command construction, event parsing, safe
  blocked envelopes, and output validation.
- Implement the runner foundation so real `codex exec` execution can be
  invoked only inside a copied runtime workspace with read-only sandbox,
  never approval, runtime output schemas, sanitized input files, safe event
  summaries, and validation-gated proposal results.
- Preserve the G05 fake runner path for existing orchestration behavior while
  adding a separately selectable real-runner foundation path.

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

Expected G07 files include:

- `spec/development/service_codex_runner_foundation.yaml`
- `services/codex-runner/runner_app/workspace.py`
- `services/codex-runner/runner_app/codex_exec.py`
- `services/codex-runner/runner_app/event_parser.py`
- `services/codex-runner/runner_app/real_runner.py`
- `services/codex-runner/runner_app/main.py`
- `services/codex-runner/runner_app/sanitizer.py`
- `services/codex-runner/runner_app/validator.py`
- focused contract/unit/security tests for the G07 runner foundation

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Runtime workspaces are created only from
  `services/codex-runner/runtime-template`, reject root Development Codex
  material, include `input`, `outputs`, and `scratch`, and contain only runtime
  docs/config/skills.
- Real runner input materialization writes only sanitized request/evidence/tool
  catalog JSON into the isolated workspace and blocks raw prompts, raw provider
  responses, row data, raw stored procedure definitions, or secrets before
  `codex exec`.
- The `codex exec` command is bound to the isolated workspace, uses approval
  `never`, sandbox `read-only`, JSON event output, a runtime-local output
  schema under `schemas/`, and writes the last message to `outputs/final.json`.
- Event parsing stores only safe event metadata and counts; raw stdout, stderr,
  prompts, provider responses, and model content are not returned for
  persistence.
- Real runner outputs pass schema and policy validation before proposal content
  is returned. Invalid, unsafe, missing, or failed executions return a
  schema-valid `BLOCKED` result with no artifact proposals.
- Service Codex Runner continues to return proposals only and does not persist
  artifacts, apply DDL/DML, execute SQL or procedures, modify source, deploy,
  or access root development skills/docs as runtime skills/docs.

## Validation commands

```bash
python -m pytest tests/contract/test_g07_service_codex_runner_foundation.py tests/unit/codex_runner/test_codex_exec_command.py tests/unit/codex_runner/test_g07_runner_foundation.py tests/security/test_cross_realm_boundary.py tests/integration/test_g01_runtime_workspace_boundary.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
