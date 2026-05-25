# Greenfield Foundation & Dual Codex Realm

## Objective

Create root and runtime documentation, configs, agents, skills, and boundary tests.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Root Development Codex Realm docs, config, agents, and skills remain explicit.
- Service Codex Runner runtime-template docs, config, agents, and skills remain separate from root Development Codex Realm assets.
- A machine-readable Dual Codex Realm contract records both realm catalogs, config expectations, boundary rules, and runtime workspace copy rules.
- Contract, integration, security, and eval tests cover the root/runtime boundary and runtime workspace construction.
- Keep documents, schemas, tests, and implementation consistent.

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

- Root docs and catalogs: `AGENTS.md`, `ARCHITECTURE.md`, `POLICY.md`, `PROJECT.md`, `EVAL_SPEC.md`, `ROLES.md`, `SKILLS.md`, `TOOLS.md`
- Development realm config/agents/skills: `.codex/config.toml`, `.codex/agents/*.toml`, `.agents/skills/*/SKILL.md`
- Runtime realm template: `services/codex-runner/runtime-template/**`
- Boundary contract: `spec/development/dual_codex_realm_contract.yaml`
- Eval suite: `spec/eval/v2_cross_realm_boundary.yaml`
- Tests: `tests/contract/test_g01_dual_codex_realm.py`, `tests/integration/test_g01_runtime_workspace_boundary.py`, `tests/security/test_cross_realm_boundary.py`, `tests/eval/test_g01_cross_realm_boundary.py`

## Acceptance criteria

- Required root and runtime docs, configs, agents, skills, contract, eval suite, and tests exist.
- Root Development Codex docs identify Development Codex as separate from Service Codex Runner.
- Runtime template docs identify Service Codex Runner as separate from Development Codex and do not inherit root development policies implicitly.
- Development and runtime skill catalogs match the filesystem and are disjoint.
- Runtime skills are runtime-scoped and do not expose root `.agents/skills` as runtime skills.
- Runtime workspaces are created from `services/codex-runner/runtime-template` only and do not copy forbidden root files or reference material.
- Runtime config blocks approval escalation, network/web search, login shell, and nested agents.
- Boundary tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.

## Validation commands

```bash
make test
```

Focused non-boundary check for this goal:

```bash
python -m pytest tests/contract/test_g01_dual_codex_realm.py tests/integration/test_g01_runtime_workspace_boundary.py tests/security/test_cross_realm_boundary.py tests/eval/test_g01_cross_realm_boundary.py
```

Full outer validation is deferred until the Foundation Complete boundary at G02.

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
