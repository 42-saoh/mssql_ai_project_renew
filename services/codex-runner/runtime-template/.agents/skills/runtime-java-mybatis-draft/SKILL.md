---
name: runtime-java-mybatis-draft
description: Create DTO, service, mapper interface, and mapper XML draft proposals.
---

# runtime-java-mybatis-draft

This is a Service Codex Runner skill. It is not a Development Codex skill.

## Inputs

- `input/run_request.json`
- `input/evidence_bundle.json`
- `schemas/java_mybatis_draft_pack.schema.json`

## Run Scope

- Allowed `runType`: `DRAFT_GENERATION`
- Allowed proposal `artifactType`: `DTO_DRAFT`, `SERVICE_DRAFT`, `MAPPER_INTERFACE`, `MAPPER_XML`
- Required output schema: `schemas/java_mybatis_draft_pack.schema.json`

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
- Java/MyBatis file proposals remain draft text only and must not include apply, write, or deploy instructions.
- Do not include raw prompt, raw provider response, row data, secrets, or executable apply instructions.

## Forbidden

- DB credential use
- SQL execution
- stored procedure execution
- DDL/DML apply
- repository source modification
- general chatbot response
