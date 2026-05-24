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

## Contract baselines

- Dual Codex Realm: `spec/development/dual_codex_realm_contract.yaml`
- OpenAPI, schemas, DB schema, and eval baseline: `spec/development/contract_schema_eval_baseline.yaml`

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

## Platform store configuration

FastAPI platform persistence uses `PLF_STORE_*` variables from `.env.example`. These settings are for the PLF platform store only, not customer or business MSSQL. The default local target is the Docker MSSQL instance on `127.0.0.1:1433`; `PLF_STORE_SCHEMA_PATH` points to `db/schema/plf_db_agent_v2.sql`, and `PLF_STORE_AUTO_APPLY_SCHEMA` defaults to `false` so schema application stays explicit.

## First Codex goal

```text
/goal Follow goals/G00-legacy-reference-freeze.md and complete the validation criteria.
```

## Release definition

V2 is complete only when G00 through G12 pass their contract, unit, integration, security, eval, and E2E gates.
