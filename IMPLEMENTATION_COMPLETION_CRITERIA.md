# Implementation Completion Criteria

V2 implementation is complete when:

1. The project is a greenfield implementation with no runtime dependency on the legacy project.
2. Development Codex and Service Codex Runner are fully separated by docs, configs, skills, workspaces, credentials, and evals.
3. Streamlit provides Chat, History, Artifact Detail, and Admin/Eval screens through FastAPI only.
4. FastAPI owns auth/RBAC, API boundary, PLF storage, validation, and runner gateway.
5. LangGraph routes all supported DB-analysis intents and blocks unsupported/general requests.
6. External MSSQL MCP/Metadata Gateway connection provides read-only metadata evidence only.
7. Service Codex Runner executes `codex exec` in isolated runtime workspaces and returns schema-valid proposals only.
8. Validation gates prevent unsafe, invalid, production-ready, raw, or executable outputs from becoming artifacts.
9. The six allowed artifact types are persisted with `production_ready=false` and visible `REVIEW_REQUIRED` markers.
10. All G00-G12 contract, unit, integration, eval, security, and E2E gates pass.
