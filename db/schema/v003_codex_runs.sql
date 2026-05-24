IF OBJECT_ID(N'dbo.codex_runs', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.codex_runs (
    codex_run_id NVARCHAR(64) NOT NULL CONSTRAINT pk_codex_runs PRIMARY KEY,
    chat_run_id NVARCHAR(64) NOT NULL,
    run_type NVARCHAR(64) NOT NULL,
    runtime_profile NVARCHAR(128) NOT NULL,
    workspace_id NVARCHAR(128) NOT NULL,
    status NVARCHAR(64) NOT NULL,
    output_schema_name NVARCHAR(128) NOT NULL,
    validation_status NVARCHAR(64) NOT NULL,
    created_at DATETIME2(3) NOT NULL,
    completed_at DATETIME2(3) NULL
  );
END;
