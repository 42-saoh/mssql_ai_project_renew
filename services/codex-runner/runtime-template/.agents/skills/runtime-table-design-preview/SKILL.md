---
name: runtime-table-design-preview
description: Create createTableScriptPreview outputs for manual review only.
---

# runtime-table-design-preview

This is a Service Codex Runner skill. It is not a Development Codex skill.

## Inputs

- `input/run_request.json`
- `input/evidence_bundle.json`
- `schemas/table_design_preview.schema.json`

## Run Scope

- Allowed `runType`: `TABLE_DESIGN`
- Allowed proposal `artifactType`: `TABLE_DESIGN_PREVIEW`
- Required output schema: `schemas/table_design_preview.schema.json`

## Procedure

1. Read the run request and evidence bundle.
2. Confirm the requested run type is in scope for this skill.
3. Use only evidence references, not raw DB access.
4. Produce schema-valid final JSON.
5. Mark uncertain or generated outputs with review markers.

## Output requirements

- `productionReady` must be `false`.
- `reviewRequired` must be `true`.
- Include evidence references for claims.
- Include `REVIEW_REQUIRED` in `reviewMarkers` and generated markdown.
- Include `previewType: TABLE_DESIGN_PREVIEW` and `blockedFromAutoApply: true`.
- `createTableScriptPreview` is a manual-review preview only; it must not include DML, procedure execution, deployment, or auto-apply instructions.
- Do not include raw prompt, raw provider response, row data, secrets, or executable apply instructions.

## Forbidden

- DB credential use
- SQL execution
- stored procedure execution
- DDL/DML apply
- repository source modification
- general chatbot response
