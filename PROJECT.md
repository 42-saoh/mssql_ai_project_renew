# Project

## Mission

Build a greenfield internal platform that turns DB-analysis-oriented natural language requests into validated, review-required artifacts.

## Product scope

Supported intents:

- `SP_ANALYSIS`
- `METADATA_SEARCH`
- `DEPENDENCY_ANALYSIS`
- `TABLE_DESIGN`
- `DRAFT_GENERATION`
- `HISTORY_LOOKUP`
- `BLOCKED_OR_APPROVAL_REQUIRED`
- `BLOCKED`

Unsupported general chat must be blocked.

## Legacy relationship

The legacy project is reference material only. V2 must not depend on legacy code at runtime and must not copy legacy implementation modules.
