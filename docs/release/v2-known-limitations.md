# V2 Known Limitations

## Release Scope

G12 acceptance is a local greenfield repository release gate. It validates the
contracts, services, runtime boundary, Streamlit FastAPI-only shell, security
policy, eval suites, and E2E acceptance flows in this repository. It does not
authorize production deployment.

## Known Limitations

- Production deployment is not performed by this release gate.
- Customer or business MSSQL row-data access remains forbidden. The platform is
  limited to read-only metadata evidence through allowlisted Metadata Gateway
  tools.
- Stored procedure execution, free SQL execution, DDL/DML apply, source apply,
  and deploy remain blocked by policy.
- The external MSSQL MCP endpoint must be an approved dev/test URL before live
  metadata smoke checks are run. G12 local tests use safe service doubles where
  needed.
- Service Codex Runner real execution requires isolated runtime workspaces
  copied from `services/codex-runner/runtime-template`, approval mode `never`,
  read-only sandbox, and output schema validation. The API integration keeps
  runner submissions proposal-only.
- Streamlit browser smoke checks are optional and gated by
  `PLF_PLAYWRIGHT_SMOKE_ENABLED=true` and `PLAYWRIGHT_BASE_URL`; screenshots,
  traces, cookies, tokens, and storage state are not release artifacts.
- Local in-memory repositories in tests are acceptance evidence for service
  behavior, not a production storage engine.
- Authentication and actor identity are minimal internal-platform scaffolding
  and must be integrated with the approved enterprise auth boundary before
  production use.
- Raw prompts, raw provider responses, raw stored procedure definitions, row
  data, connection strings, source content, runner stdout/stderr, and secrets
  must not be persisted in any future production adapter.

## Non-Exceptions

These limitations do not weaken the V2 policy. Streamlit calls FastAPI only,
Service Codex Runner returns proposals only, validation gate controls artifact
persistence, and there is no row data, no stored procedure execution, no
DDL/DML apply, no source apply, no deploy, no raw prompt persistence, no raw
provider response persistence, and no secret persistence.
