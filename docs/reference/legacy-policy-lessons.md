# Legacy Policy Lessons

V2 carries forward the following policy boundaries from the legacy review, but
implements them from scratch.

Blocked operations and storage:

- no row-data query or display
- no stored procedure execution
- no free SQL execution
- no DDL or DML apply
- no automatic source apply
- no deploy
- no raw prompt persistence
- no raw provider response persistence
- no raw SP definition persistence
- no row data persistence
- no secret persistence
- no general chatbot answers outside DB analysis scope

Required controls:

- Streamlit calls FastAPI only.
- Service Codex Runner returns proposals only.
- Validation gates control artifact persistence.
- Generated artifacts are saved with `production_ready=false`.
- Review markers remain visible in generated artifacts.
- Development Codex and Service Codex Runner do not share docs, skills,
  workspaces, credentials, or audit boundaries.
