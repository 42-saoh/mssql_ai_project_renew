# Scaffold Status

Generated scaffold for `plf-db-agent-v2`.

## Included

- Development Codex Realm docs/config/agents/skills at repo root
- Service Codex Runner Realm docs/config/agents/skills under `services/codex-runner/runtime-template/`
- G00-G12 goal files
- Legacy reference-only docs
- FastAPI skeleton
- Streamlit skeleton
- LangGraph-style orchestration skeleton
- External MSSQL MCP/Metadata Gateway connector skeleton
- Service Codex Runner skeleton with fake/real boundary
- OpenAPI draft, JSON schemas, DB schema drafts, eval specs
- Contract/unit/security/integration/eval/e2e smoke tests

## Verification performed

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH=packages/contracts/src:packages/orchestration/src:packages/validation/src:services/codex-runner:services/codex_runner:apps/api \
python -m pytest tests -q
```

Result:

```text
22 passed
```

## Scope note

This is the greenfield V2 repository scaffold and contract baseline. It is ready for Codex CLI goal-driven implementation from G00 through G12, but it is not the completed production platform yet.
