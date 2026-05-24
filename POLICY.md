# V2 Policy

## Core safety policy

V2 is a DB analysis and draft generation platform. It does not execute business operations.

Always forbidden:

- Row data query or display
- Stored procedure execution
- Free SQL execution
- Business DB DDL/DML application
- Automatic create/alter/drop application
- Source apply or deploy
- Raw prompt persistence
- Raw provider response persistence
- Secret persistence
- General chatbot answers outside DB analysis scope

## Allowed behavior

- Read-only metadata search
- Dependency evidence retrieval through allowlisted metadata tools
- Artifact proposal generation in isolated runner workspaces
- Manual-review table design previews
- Manual-review Java/MyBatis draft proposals
- Sanitized history and artifact storage after validation

## Artifact policy

Allowed public artifact types:

- `SP_ANALYSIS_DOC`
- `DEPENDENCY_REPORT`
- `DTO_DRAFT`
- `SERVICE_DRAFT`
- `MAPPER_INTERFACE`
- `MAPPER_XML`

Retired or blocked public artifact types:

- `DDL_DRAFT`
- `VO_DRAFT`
- `MODEL_DRAFT`

All generated artifacts must be saved with `production_ready=false`. Review markers must remain visible.
