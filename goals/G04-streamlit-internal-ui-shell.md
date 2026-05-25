# Streamlit Internal UI Shell

## Objective

Implement Chat, History, Artifact Detail, and Admin/Eval UI through FastAPI only.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G04 Streamlit shell contract that maps Chat,
  History, Artifact Detail, and Admin/Eval pages to FastAPI-only client
  methods.
- Implement the Streamlit internal shell pages using the root `DESIGN.md`
  contract, `.streamlit/config.toml`, and `styles/design.css`.
- Route all Streamlit platform data access through
  `apps.streamlit.client.api_client.ApiClient`; no Streamlit page may call
  DB, MSSQL MCP, Metadata Gateway, or Service Codex Runner directly.
- Show generated or persisted artifact material only as draft/manual-review
  metadata with visible validation or blocker state.

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

Expected G04 files include:

- `spec/development/streamlit_internal_ui_shell.yaml`
- `apps/streamlit/app.py`
- `apps/streamlit/pages/01_Chat.py`
- `apps/streamlit/pages/02_History.py`
- `apps/streamlit/pages/03_Artifact_Detail.py`
- `apps/streamlit/pages/04_Admin_Eval.py`
- `apps/streamlit/client/api_client.py`
- `.streamlit/config.toml`
- `styles/design.css`
- focused contract/unit/security tests for the Streamlit API-only shell

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Chat, History, Artifact Detail, and Admin/Eval pages use `ApiClient` for
  FastAPI calls and do not import or invoke DB, MCP, Metadata Gateway, or
  Service Codex Runner modules.
- The Streamlit shell follows `DESIGN.md`: wide layout, expanded sidebar,
  restrained monochrome theme, stable CSS utilities, visible empty/error
  states, and review-state badges.
- Artifact previews and exports are labeled as draft or manual-review material;
  production-ready, execute, apply, deploy, row-data, and stored-procedure
  execution actions are absent.
- Admin/Eval diagnostics remain development-console status views only and do
  not persist raw prompts, raw provider responses, SP definitions, row data, or
  secrets.

## Validation commands

```bash
python -m pytest tests/contract/test_g04_streamlit_internal_ui_shell.py tests/contract/test_streamlit_design_contract.py tests/security/test_streamlit_design_boundary.py tests/unit/test_streamlit_api_client.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
