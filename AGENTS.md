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
- Keep implementation small and explicit.
- Add tests with each behavior change.
- Avoid hidden side effects.
- Do not copy implementation code from the legacy project.

## Stop immediately if

- A change weakens no row-data, no procedure execution, no DDL/DML apply, no source apply, or no deploy policy.
- A Service Codex Runner path can read root `.agents/skills` as runtime skills.
- Streamlit directly calls DB, MCP, or Codex Runner.
- Raw prompts, raw provider responses, raw SP definitions, row data, or secrets would be persisted.
