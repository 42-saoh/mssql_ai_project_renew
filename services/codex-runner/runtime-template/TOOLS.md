# Runtime Tools

Allowed read-only metadata tools, when included in `input/tool_catalog.json`:

- `search_tables`
- `search_columns`
- `get_table_schema`
- `get_procedure_signature`
- `get_procedure_dependencies`
- `find_similar_objects`

Blocked tools:

- `execute_sql`
- `execute_procedure`
- `query_row_data`
- `apply_ddl`
- `apply_dml`
- `deploy_source`
