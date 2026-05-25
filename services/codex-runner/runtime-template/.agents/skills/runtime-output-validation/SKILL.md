---
name: runtime-output-validation
description: Validate output structure, evidence references, review markers, and productionReady=false.
---

# runtime-output-validation

This is a Service Codex Runner skill. It is not a Development Codex skill.

## Inputs

- `input/run_request.json`
- `input/evidence_bundle.json`
- `schemas/output.schema.json`
- The requested run-specific schema under `schemas/`

## Run Scope

- Validator-only skill for every allowed runtime run type.
- It must not create domain content by itself.
- It checks the final JSON for schema-valid, policy-valid, and static-validation-passed flags.

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
- Include `REVIEW_REQUIRED` in `reviewMarkers` and generated markdown for every proposal.
- Set `schemaValid`, `policyValid`, and `staticValidationPassed` to `false` when any blocker exists.
- Do not include raw prompt, raw provider response, row data, secrets, or executable apply instructions.

## Forbidden

- DB credential use
- SQL execution
- stored procedure execution
- DDL/DML apply
- repository source modification
- general chatbot response
