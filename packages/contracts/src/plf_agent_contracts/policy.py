from __future__ import annotations

DEFAULT_BLOCKED_OPERATIONS = {
    "row_data_query",
    "stored_procedure_execution",
    "free_sql_execution",
    "ddl_dml_apply",
    "source_apply",
    "deploy",
    "raw_prompt_storage",
    "raw_provider_response_storage",
    "secret_storage",
    "general_chat",
}

DEFAULT_RUNTIME_POLICY = {
    "allowRowData": False,
    "allowProcedureExecution": False,
    "allowDdlDmlApply": False,
    "allowSourceApply": False,
    "allowDeploy": False,
    "allowRawPromptStorage": False,
    "allowRawProviderResponseStorage": False,
}
