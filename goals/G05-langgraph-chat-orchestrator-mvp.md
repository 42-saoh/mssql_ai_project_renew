# LangGraph Chat Orchestrator MVP

## Objective

Implement domain guard, intent routing, policy gate, checkpoint state, and fake runner routing.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G05 LangGraph orchestrator contract covering
  domain guard, intent routing, policy gate, sanitized checkpoint state, and
  fake runner routing.
- Implement the chat orchestrator as a LangGraph `StateGraph` with explicit
  domain guard, policy gate, optional PGPT intent assist, route selection, and
  fake-runner request preparation nodes.
- Persist only sanitized orchestrator checkpoint state through the FastAPI
  chat service; do not persist raw user messages, raw prompts, raw provider
  responses, row data, stored procedure definitions, or secrets.
- Route allowed artifact-generation intents to the fake runner gateway without
  persisting fake runner proposal content or artifacts in G05.

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

Expected G05 files include:

- `spec/development/langgraph_chat_orchestrator_mvp.yaml`
- `packages/orchestration/src/plf_agent_orchestration/graph.py`
- `packages/orchestration/src/plf_agent_orchestration/state.py`
- `packages/orchestration/src/plf_agent_orchestration/intents.py`
- `apps/api/api_app/services/chat_service.py`
- `apps/api/api_app/services/codex_runner_client.py`
- focused contract/unit/integration/eval tests for the G05 orchestrator MVP

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- The orchestrator uses LangGraph state nodes for domain guard, policy gate,
  PGPT intent assist, route selection, and fake runner request preparation.
- General chat is blocked before PGPT, metadata gateway, fake runner
  submission, approval side effects, or artifact persistence.
- DB-themed explanatory/general chat, such as `What is SQL?`,
  `Explain databases`, and `What is a column?`, is also blocked before PGPT,
  metadata gateway, fake runner submission, approval side effects, or artifact
  persistence unless it has a supported DB-analysis action or concrete
  metadata/object lookup shape.
- Stored procedure execution, free SQL execution, row-data access, source
  apply, and deploy requests hard-block before PGPT, metadata gateway, fake
  runner submission, approval side effects, or artifact persistence.
- Allowed DB-analysis intents route only to approved boundaries:
  `codex_runner`, `metadata_gateway`, or `history_store`.
- Persisted chat run state contains only sanitized message summaries and the
  sanitized orchestrator checkpoint; raw user messages, raw prompts, raw
  provider responses, row data, stored procedure definitions, and secrets are
  absent.
- Fake runner routing records only submission and validation metadata in G05;
  fake runner proposal content and artifacts are not persisted.

## Validation commands

```bash
python -m pytest tests/contract/test_g05_langgraph_chat_orchestrator_mvp.py tests/unit/orchestration/test_g05_langgraph_mvp.py tests/integration/test_g05_chat_orchestrator_mvp.py tests/eval/test_g05_orchestrator_mvp_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
