# Legacy Artifact Taxonomy

V2 keeps only the artifact categories that can be produced as review-required
proposals without implying DB execution, source apply, or deployment.

Allowed V2 public artifact types:

- SP_ANALYSIS_DOC
- DEPENDENCY_REPORT
- DTO_DRAFT
- SERVICE_DRAFT
- MAPPER_INTERFACE
- MAPPER_XML

Retired or blocked public artifact types:

- DDL_DRAFT
- VO_DRAFT
- MODEL_DRAFT

Preview-only outputs:

- TABLE_DESIGN_PREVIEW

`TABLE_DESIGN_PREVIEW` may exist only as a manual-review preview. It is not a
public persisted artifact type and must not include automatic DDL apply
language.

All generated artifacts must keep `production_ready=false`, visible
`REVIEW_REQUIRED` markers, and evidence references for claims.
