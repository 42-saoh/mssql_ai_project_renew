---
name: runtime-policy-review
description: Detect blocked operations, raw payload leakage, secrets, and unsafe persistence candidates.
---

# runtime-policy-review

This is a Service Codex Runner skill. It is not a Development Codex skill.

## Inputs

- `input/run_request.json`
- `input/evidence_bundle.json`
- `schemas/output.schema.json`
- The requested run-specific schema under `schemas/`

## Run Scope

- Policy-review skill for every allowed runtime run type.
- It must not create domain content by itself.
- It reviews proposals for blocked operations, redaction leaks, unsafe persistence candidates, and missing review markers.

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
- Any policy blocker must produce or preserve a `BLOCKED` result with no artifact proposals.
- Do not include raw prompt, raw provider response, row data, secrets, or executable apply instructions.

## Forbidden

- DB credential use
- SQL execution
- stored procedure execution
- DDL/DML apply
- repository source modification
- general chatbot response
