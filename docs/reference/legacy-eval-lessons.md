# Legacy Eval Lessons

V2 evals must catch:

- fallback skeleton artifacts being persisted
- schema-invalid runner results being persisted
- raw SP or prompt leakage
- hidden REVIEW_REQUIRED markers
- dependency evidence without caveats
- table design outputs that imply automatic DDL application

The G00 freeze contract maps each lesson to an eval suite and case id in
`spec/reference/legacy_reference_freeze.yaml`. The relevant suites are:

- `v2_artifact_quality`
- `v2_runner_output_schema`
- `v2_storage_redaction`
- `v2_runner_policy`
- `v2_cross_realm_boundary`
- `v2_mssql_mcp_readonly`
- `v2_blocked_request_paths`

These evals protect the reference boundary as well as the product behavior:
legacy lessons can define what V2 must prevent, but they must not import legacy
implementation patterns into the runtime.
