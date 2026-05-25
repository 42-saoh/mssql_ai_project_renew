# V2 Implementation Plan

Phases:

1. G00 Legacy Reference Freeze
2. G01 Greenfield Foundation & Dual Codex Realm
3. G02 Contract / Schema / Eval Baseline
4. G03 FastAPI Platform Core
5. G04 Streamlit Internal UI Shell
6. G05 LangGraph Chat Orchestrator MVP
7. G06 MSSQL MCP / Metadata Gateway
8. G07 Service Codex Runner Foundation
9. G08 Runtime Skills / Output Schemas / Validators
10. G09 Domain Feature Integration
11. G10 Artifact / History / Approval UX Completion
12. G11 Security / Eval / Observability Hardening
13. G12 End-to-End Acceptance & V2 Release

## Release Artifacts

G12 publishes the final local release artifacts:

- `spec/development/end_to_end_acceptance_release.yaml`
- `spec/eval/v2_end_to_end_happy_paths.yaml`
- `docs/release/v2-acceptance-report.md`
- `docs/release/v2-security-report.md`
- `docs/release/v2-eval-report.md`
- `docs/release/v2-runbook.md`
- `docs/release/v2-known-limitations.md`

The release remains bounded by the V2 policy: Streamlit calls FastAPI only,
Service Codex Runner returns proposals only, validation gate controls artifact
persistence, no row data, no stored procedure execution, no DDL/DML apply, no
source apply, no deploy, no raw prompt persistence, no raw provider response
persistence, and no secret persistence.
