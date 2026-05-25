# Runtime Skill Catalog

Runtime skills are service-only skills and must use `runtime-*` names.

- `runtime-sp-analysis`: `SP_ANALYSIS` to `SP_ANALYSIS_DOC`, schema `schemas/sp_analysis_result.schema.json`
- `runtime-dependency-analysis`: `DEPENDENCY_ANALYSIS` to `DEPENDENCY_REPORT`, schema `schemas/dependency_analysis_result.schema.json`
- `runtime-table-design-preview`: `TABLE_DESIGN` to `TABLE_DESIGN_PREVIEW`, schema `schemas/table_design_preview.schema.json`
- `runtime-java-mybatis-draft`: `DRAFT_GENERATION` to Java/MyBatis draft proposal types, schema `schemas/java_mybatis_draft_pack.schema.json`
- `runtime-output-validation`: validator-only schema, policy, and static checks
- `runtime-policy-review`: validator-only blocked-operation and redaction checks

Do not use root development skills inside service runtime workspaces.
