# Repository Manifest

This archive contains the initial greenfield scaffold for **PLF DB Agent V2**.

## Included

- Root Development Codex Realm docs: `AGENTS.md`, `POLICY.md`, `PROJECT.md`, `ARCHITECTURE.md`, `EVAL_SPEC.md`, `ROLES.md`, `SKILLS.md`, `TOOLS.md`.
- Root `.codex/agents` and `.agents/skills` for development-only Codex CLI `/goal` work.
- Service Codex Runner runtime-template with separate docs, `.codex`, runtime agents, runtime skills, and runtime schemas.
- G00~G12 goal files.
- Streamlit shell, FastAPI shell, orchestration package, validation package, contracts package, Codex Runner service, and MSSQL metadata gateway scaffold.
- OpenAPI, JSON schemas, MCP tool catalog, eval specs, and DB schema scaffolds.
- Contract, unit, integration, eval, security, and E2E smoke tests.

## Excluded by design

- Legacy project implementation code.
- Runtime DB credentials.
- Row data fixtures.
- Generated caches and `__pycache__` files.
