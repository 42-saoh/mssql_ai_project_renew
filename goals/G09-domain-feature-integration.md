# Domain Feature Integration

## Objective

Connect supported intents to metadata, history, and Codex Runner flows.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G09 domain feature integration contract that maps
  supported intents to metadata, history, and Codex Runner boundaries.
- Connect allowed metadata-search chat runs to the Metadata Gateway search
  service without Codex Runner, approval, or artifact-persistence side effects.
- Connect allowed history lookups to sanitized chat-run history only; raw user
  messages, raw prompts, provider responses, row data, SP definitions, and
  secrets must not be persisted or returned.
- Connect runner-backed intents to schema-aware Service Codex Runner request
  metadata, including runtime skill allowlists, requested output schemas, safe
  target refs, and all runtime policy flags false.

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

Expected G09 files include:

- `spec/development/domain_feature_integration.yaml`
- `apps/api/api_app/services/chat_service.py`
- `apps/api/api_app/services/codex_runner_client.py`
- focused contract/integration tests for metadata, history, and runner domain
  feature integration

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- `METADATA_SEARCH` chat runs invoke only
  `metadata_service.search_metadata` / `search_metadata_objects`, persist no
  external metadata response payload, submit no Codex Runner run, create no
  approval, and persist no artifacts.
- `HISTORY_LOOKUP` chat runs return only sanitized prior run summaries from the
  history store for the conversation and do not call Metadata Gateway, Codex
  Runner, approval, or artifact persistence.
- `SP_ANALYSIS`, `DEPENDENCY_ANALYSIS`, `TABLE_DESIGN`, and
  `DRAFT_GENERATION` chat runs submit runner request metadata with the
  G08-requested runtime output schema and service-only runtime skill allowlist
  for the intent.
- Runner submissions remain proposal-only metadata in G09; proposal content and
  artifacts are not persisted.
- Blocked, out-of-domain, row-data, procedure-execution, free-SQL,
  source-apply, and deploy requests still hard-block before Metadata Gateway
  proxying, runner submission, approval side effects, or artifact persistence
  as required by previous goals.
- DDL/DML-apply requests remain policy-review gated as required by previous
  goals and do not reach Metadata Gateway proxying, runner submission, or
  artifact persistence.

## Validation commands

```bash
python -m pytest tests/contract/test_g09_domain_feature_integration.py tests/integration/test_g09_domain_flows.py tests/integration/test_g09_domain_routing_scaffold.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
