# PLF DB Agent V2

Greenfield DB analysis agent platform.

This repository is intentionally **not** a migration of the legacy project. The legacy project is reference material only. V2 is implemented from scratch around:

- Streamlit internal Chat UI and History/Artifact screens
- FastAPI API/service boundary
- LangGraph chat orchestration
- PGPT Responses API boundary for optional chat orchestration assistance
- External MSSQL MCP / Metadata Gateway connection for read-only metadata evidence
- Service Codex Runner for isolated heavy artifact generation
- Dual Codex Realm separation

## Two Codex realms

| Realm | Purpose | Execution |
|---|---|---|
| Development Codex Realm | Build and maintain this repository | Codex CLI `/goal` |
| Service Codex Runner Realm | Generate service artifact proposals | `codex exec` inside isolated runtime workspaces |

The two realms must never share docs, config, skills, workspaces, credentials, or audit boundaries.
The enforceable boundary contract is `spec/development/dual_codex_realm_contract.yaml`.

## Start development

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e packages/contracts -e packages/orchestration -e packages/validation
pip install -r requirements-dev.txt
make test
```

## PGPT configuration

User chat orchestration can optionally call PGPT through the OpenAI-compatible Responses API. Configure it with `PGPT_BASE_URL`, `PGPT_MODEL`, and `PGPT_API_KEY`; see `docs/reference/pgpt-responses-api.md` for the supported parameter allowlist and safety limits.

## First Codex goal

```text
/goal Follow goals/G00-legacy-reference-freeze.md and complete the validation criteria.
```

## Release definition

V2 is complete only when G00 through G12 pass their contract, unit, integration, security, eval, and E2E gates.
