# Development Codex Realm Instructions

You are operating in the **Development Codex Realm**. Your job is to build and maintain the PLF DB Agent V2 repository.

## Hard boundary

Development Codex is not Service Codex Runner.

- Development Codex uses the root repository, root `.codex`, root `.agents/skills`, and root documents.
- Service Codex Runner uses only `services/codex-runner/runtime-template/*` copied into isolated runtime workspaces.
- Do not treat runtime skills as development skills unless a goal explicitly asks you to edit their source files.
- Do not let service runtime documents inherit root development policies implicitly.

## Development method

Use `goals/Gxx-*.md` files and Codex CLI `/goal`.

Every goal must include:

- Objective
- Context
- Required deliverables
- Non-goals
- Constraints
- Files to create or modify
- Acceptance criteria
- Validation commands
- Stop conditions
- Report format

## Coding rules

- Contract-first.
- Eval-first.
- Policy-first.
- For Streamlit UI, CSS, layout, form, chart, or generated-output preview changes, read root `DESIGN.md` first and follow it as the authoritative UI design contract.
- Use `.agents/skills/context7-docs` only when current framework, library, API, configuration, migration, or CLI documentation is needed; do not send secrets, credentials, connection strings, raw prompts, provider responses, or large proprietary code to external documentation tools.
- Use `.agents/skills/browser-automation-smoke` only for non-destructive Playwright smoke checks against localhost or approved dev/test URLs; do not commit cookies, tokens, screenshots, traces, or storage state.
- Keep implementation small and explicit.
- Add tests with each behavior change.
- Avoid hidden side effects.
- Do not copy implementation code from the legacy project.

## Stop immediately if

- A change weakens no row-data, no procedure execution, no DDL/DML apply, no source apply, or no deploy policy.
- A Service Codex Runner path can read root `.agents/skills` as runtime skills.
- Streamlit directly calls DB, MCP, or Codex Runner.
- Raw prompts, raw provider responses, raw SP definitions, row data, or secrets would be persisted.

## Strict sequential goals workflow

When the user asks to run goals in `goals/`, follow this contract:

- Goal files are ordered lexicographically by filename: `G00`, `G01`, `G02`, ...
- Never execute a later goal before all earlier goals are completed; previous completed stages must remain validated.
- Execute exactly one goal at a time.
- Outer validation gates run at stage boundaries only:
  - Foundation Complete: `G00`, `G01`, `G02`
  - MVP Complete: `G03`, `G04`, `G05`, `G06`, `G07`
  - Feature Complete: `G08`, `G09`, `G10`
  - Release Complete: `G11`, `G12`
- Between stage boundaries, keep goals sequential but defer full outer validation until the current stage boundary.
- If any previous goal is incomplete, broken, or inconsistent, return to the earliest failing goal and resume sequentially from there.
- Treat previous goals as regression contracts.
- If a completed previous stage regresses, completion requires concrete changed files or a strengthened implementation, test, spec, or goal-document contract that repairs or captures the regression.
- Do not copy legacy implementation code.
- Do not weaken blocked-operation policy.
- Do not merge Development Codex and Service Codex Runner realms.
- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Validation gate controls artifact persistence.
- No row data, SP execution, DDL/DML apply, source apply, deploy, or raw prompt/provider storage.
- Completion requires acceptance criteria, validation commands, and policy boundaries to pass.

Prefer using `scripts/codex-strict-goal-runner.py` for unattended execution instead of relying on prompt-only sequencing.
