# Artifact / History / Approval UX Completion

## Objective

Complete artifact/history/validation/approval APIs and Streamlit UX.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G10 artifact/history/approval UX completion
  contract covering artifact validation APIs, sanitized history APIs, approval
  review APIs, Streamlit FastAPI-only client methods, and review-state UX.
- Complete artifact APIs so validated runner proposals can be persisted only
  after schema/policy/static validation, with content stored by reference/hash
  only, `production_ready=false`, `review_required=true`, review markers,
  evidence refs, and validation records visible through API detail views.
- Complete sanitized history APIs for conversation lists and conversation
  details without raw user messages, raw prompts, raw provider responses, row
  data, raw stored procedure definitions, or secrets.
- Complete approval review APIs and Streamlit UX so approval resume updates
  review metadata only and never triggers DB execution, runner submission,
  artifact persistence, source apply, or deploy side effects.
- Update Streamlit History and Artifact Detail views through
  `apps.streamlit.client.api_client.ApiClient` only, following `DESIGN.md`,
  with visible `DRAFT`, `MANUAL REVIEW REQUIRED`, `VALIDATED`, `BLOCKED`,
  `FAILED`, `PENDING`, and `RESUMED` states where relevant.

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

Expected G10 files include:

- `spec/development/artifact_history_approval_ux_completion.yaml`
- `spec/eval/v2_artifact_history_approval_ux.yaml`
- `spec/openapi/plf_db_agent_v2_openapi.yaml`
- `apps/api/api_app/routes/artifacts.py`
- `apps/api/api_app/routes/approvals.py`
- `apps/api/api_app/routes/conversations.py`
- `apps/api/api_app/services/artifact_service.py`
- `apps/api/api_app/services/approval_service.py`
- `apps/api/api_app/services/chat_service.py`
- `apps/streamlit/client/api_client.py`
- `apps/streamlit/pages/02_History.py`
- `apps/streamlit/pages/03_Artifact_Detail.py`
- focused contract/unit/integration/security/eval tests for G10 completion

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- G10 contract and OpenAPI declare the completed artifact, validation,
  sanitized history, and approval review endpoints.
- Validated artifact proposal persistence creates only draft/manual-review
  artifact metadata and validation records; inline artifact content,
  production-ready artifacts, table design previews, retired artifact types,
  raw prompts, raw provider responses, row data, raw stored procedure
  definitions, and secrets are not persisted or returned.
- Artifact detail APIs expose validation status and validation records with
  safe blocker codes only.
- History APIs return sanitized conversation/run summaries only and do not
  return raw user messages, raw prompts, raw provider responses, row data, raw
  stored procedure definitions, or secrets.
- Approval review APIs can list, inspect, and resume review records, but resume
  has no DB execution, runner submission, artifact persistence, source apply,
  deploy, or raw-payload persistence side effects.
- Streamlit History and Artifact Detail UX use `ApiClient` FastAPI methods for
  history, artifact, validation, and approval data; no page imports or invokes
  DB, MSSQL MCP, Metadata Gateway, or Service Codex Runner modules directly.
- Streamlit review UX follows `DESIGN.md`, keeps review states visible, and
  avoids unsafe action labels such as execute, apply, deploy, run stored
  procedure, auto-fix, or overwrite source.

## Validation commands

```bash
python -m pytest tests/contract/test_g10_artifact_history_approval_ux_completion.py tests/unit/api/test_g10_artifact_history_approval_services.py tests/integration/test_g10_artifact_history_approval_routes.py tests/security/test_g10_artifact_history_approval_policy.py tests/eval/test_g10_artifact_history_approval_ux_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
