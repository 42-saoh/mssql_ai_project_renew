# Runtime Skills / Output Schemas / Validators

## Objective

Implement runtime skills, output schemas, and policy/static/redaction validators.

## Context

PLF DB Agent V2 is a greenfield implementation. Legacy code is reference-only. Development Codex and Service Codex Runner are separate realms.

## Required deliverables

- Update or create files required for this phase.
- Add contract/unit/integration/security/eval tests appropriate to this phase.
- Keep documents, schemas, and implementation consistent.
- Define a machine-readable G08 runtime skills/output schemas/validators
  contract that maps every runtime skill to its allowed run type, output
  schema, artifact proposal type(s), and validator responsibilities.
- Specialize Service Codex Runner runtime output schemas for SP analysis,
  dependency analysis, table design previews, and Java/MyBatis draft
  generation while keeping the generic result schema available.
- Implement requested output-schema validation after `codex exec` returns
  `outputs/final.json`; generic-schema-valid but run-specific-schema-invalid
  results must return a schema-valid `BLOCKED` result with no proposals.
- Enforce policy, static, and redaction validators for generated proposals,
  including visible review markers, preview-only table design blockers,
  Java/MyBatis draft review markers, executable instruction blockers, and
  row-data/raw-payload/secret redaction blockers.

## Non-goals

- Do not copy legacy implementation code.
- Do not weaken blocked-operation policy.
- Do not merge Development Codex and Service Codex Runner realms.

## Constraints

- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Validation gate controls artifact persistence.
- No row data, SP execution, DDL/DML apply, source apply, deploy, raw prompt/provider storage.

## Files to create or modify

See the phase plan in `docs/release/v2-implementation-plan.md` after G12, or the root `README.md` for the phase list.

Expected G08 files include:

- `spec/development/runtime_skills_output_schemas_validators.yaml`
- `spec/eval/v2_runtime_output_validation.yaml`
- `services/codex-runner/runtime-template/.agents/skills/runtime-*/SKILL.md`
- `services/codex-runner/runtime-template/SKILLS.md`
- `services/codex-runner/runtime-template/schemas/*_result.schema.json`
- `services/codex-runner/runtime-template/schemas/java_mybatis_draft_pack.schema.json`
- `services/codex-runner/runtime-template/schemas/table_design_preview.schema.json`
- `services/codex-runner/runner_app/validator.py`
- `packages/validation/src/plf_agent_validation/policy_validator.py`
- `packages/validation/src/plf_agent_validation/java_mybatis_validator.py`
- `packages/validation/src/plf_agent_validation/sql_preview_validator.py`
- focused contract/unit/eval tests for runtime skills, schemas, and validators

## Acceptance criteria

- Required deliverables exist.
- Tests for this phase pass.
- No hard fail condition from `EVAL_SPEC.md` is introduced.
- Runtime skills remain service-only `runtime-*` skills under
  `services/codex-runner/runtime-template/.agents/skills`, and each
  domain-generation skill declares exactly one allowed run type, requested
  output schema, and allowed proposal artifact type set.
- Runtime-specific output schemas constrain run type and proposal artifact
  type(s), require `productionReady: false`, `reviewRequired: true`,
  evidence refs, review markers, and visible `REVIEW_REQUIRED` generated
  content.
- Table design preview outputs remain preview-only, require
  `blockedFromAutoApply: true`, and cannot be treated as persisted public
  artifacts.
- The runner validates returned final JSON against both the generic runner
  result schema and the requested runtime output schema before returning
  proposal content.
- Policy/static/redaction validators block executable apply/deploy/procedure
  instructions, unsafe table previews, Java/MyBatis drafts without review
  markers, row data, raw prompts, raw provider responses, raw stored procedure
  definitions, connection strings, and secrets.
- Invalid, unsafe, or schema-mismatched runner outputs return a schema-valid
  `BLOCKED` result with no artifact proposals and safe blocker codes only.

## Validation commands

```bash
python -m pytest tests/contract/test_g08_runtime_skills_output_schemas_validators.py tests/unit/validation/test_g08_runtime_validators.py tests/unit/codex_runner/test_g08_runtime_schema_validation.py tests/eval/test_g08_runtime_output_validation_eval.py -q
make test
```

## Stop conditions

Stop when the acceptance criteria pass and a concise change report can be written.

## Report format

- Changed files
- Validation commands and results
- Policy boundary notes
- Remaining risks
