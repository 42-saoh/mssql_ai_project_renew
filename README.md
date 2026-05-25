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

Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e packages/contracts -e packages/orchestration -e packages/validation
python -m pip install -r requirements-dev.txt
python .\scripts\codex-strict-goal-runner.py --workspace . --goals-dir goals --sandbox workspace-write --approval never --auto-commit
```

On Windows, the strict goal runner attempts to discover validation tools with the same PowerShell lookup used in an interactive shell:

```powershell
$python = (Get-Command python).Source
$makeCommand = Get-Command make
$makeItem = Get-Item $makeCommand.Source
$make = if ($makeItem.Target) { $makeItem.Target[0] } else { $makeCommand.Source }
```

If Codex validation runs under a sandbox account that cannot resolve your interactive `python` or `make`, pass the discovered paths explicitly:

```powershell
python .\scripts\codex-strict-goal-runner.py `
  --workspace . `
  --goals-dir goals `
  --sandbox workspace-write `
  --approval never `
  --auto-commit `
  --validation-python $python `
  --validation-make $make
```

The same settings can be supplied with `CODEX_GOAL_RUNNER_PYTHON`, `CODEX_GOAL_RUNNER_MAKE`, and `CODEX_GOAL_RUNNER_PATH_PREPEND`. Use `--no-validation-tool-autodiscover` when you want validation to use only the inherited environment and explicit flags.

Goal validation currently calls `make test`, so Windows environments also need a working GNU Make executable on `PATH`. The strict goal runner executes outer validation at stage boundaries only:

- Foundation Complete: G00 through G02
- MVP Complete: G03 through G07
- Feature Complete: G08 through G10
- Release Complete: G11 through G12

At each boundary the runner deduplicates identical validation commands across completed goals before running them.
If boundary validation or semantic verification rolls back to an earlier goal, the next retry must produce concrete git-detected changes in implementation, tests, specs, scripts, database schema, or root goal documents. Self-reported `changed_files` alone is not enough; the runner rejects no-op rollback retries.

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
