-- PLF DB Agent V2 platform storage schema for SQL Server.
--
-- Scope:
-- - Apply only to the PLF platform storage database used by this application.
-- - Connect to the target platform database before running this file.
-- - Do not apply this file to customer/business MSSQL databases.
-- - Do not add raw prompt, raw provider response, raw stored procedure,
--   row-data, credential, source-apply, or deploy storage columns.

IF OBJECT_ID(N'dbo.conversations', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.conversations (
    conversation_id NVARCHAR(64) NOT NULL CONSTRAINT pk_conversations PRIMARY KEY,
    actor_id NVARCHAR(128) NOT NULL,
    title NVARCHAR(256) NULL,
    created_at DATETIME2(3) NOT NULL,
    updated_at DATETIME2(3) NOT NULL
  );
END;

IF OBJECT_ID(N'dbo.chat_runs', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.chat_runs (
    chat_run_id NVARCHAR(64) NOT NULL CONSTRAINT pk_chat_runs PRIMARY KEY,
    conversation_id NVARCHAR(64) NOT NULL,
    user_message_summary NVARCHAR(1024) NOT NULL,
    intent NVARCHAR(64) NOT NULL,
    status NVARCHAR(64) NOT NULL,
    policy_decision NVARCHAR(64) NOT NULL,
    target_key NVARCHAR(256) NULL,
    created_at DATETIME2(3) NOT NULL,
    completed_at DATETIME2(3) NULL
  );
END;

IF OBJECT_ID(N'dbo.artifacts', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.artifacts (
    artifact_id NVARCHAR(64) NOT NULL CONSTRAINT pk_artifacts PRIMARY KEY,
    chat_run_id NVARCHAR(64) NOT NULL,
    codex_run_id NVARCHAR(64) NULL,
    artifact_type NVARCHAR(64) NOT NULL,
    title NVARCHAR(256) NOT NULL,
    content_ref NVARCHAR(512) NOT NULL,
    content_hash CHAR(64) NOT NULL,
    production_ready BIT NOT NULL CONSTRAINT df_artifacts_production_ready DEFAULT (0),
    review_required BIT NOT NULL CONSTRAINT df_artifacts_review_required DEFAULT (1),
    created_at DATETIME2(3) NOT NULL
  );
END;

IF OBJECT_ID(N'dbo.artifact_validations', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.artifact_validations (
    validation_id NVARCHAR(64) NOT NULL CONSTRAINT pk_artifact_validations PRIMARY KEY,
    artifact_id NVARCHAR(64) NOT NULL,
    schema_valid BIT NOT NULL,
    policy_valid BIT NOT NULL,
    static_valid BIT NOT NULL,
    blocker_codes NVARCHAR(MAX) NOT NULL,
    review_markers NVARCHAR(MAX) NOT NULL,
    created_at DATETIME2(3) NOT NULL
  );
END;

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

IF OBJECT_ID(N'dbo.approval_requests', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.approval_requests (
    approval_id NVARCHAR(64) NOT NULL CONSTRAINT pk_approval_requests PRIMARY KEY,
    chat_run_id NVARCHAR(64) NOT NULL,
    approval_type NVARCHAR(64) NOT NULL,
    status NVARCHAR(64) NOT NULL,
    reason NVARCHAR(512) NOT NULL,
    requested_at DATETIME2(3) NOT NULL,
    resolved_at DATETIME2(3) NULL
  );
END;

IF OBJECT_ID(N'dbo.evidence_bundles', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.evidence_bundles (
    evidence_bundle_id NVARCHAR(64) NOT NULL CONSTRAINT pk_evidence_bundles PRIMARY KEY,
    db_profile_id NVARCHAR(128) NOT NULL,
    target_key NVARCHAR(256) NOT NULL,
    evidence_hash CHAR(64) NOT NULL,
    content_ref NVARCHAR(512) NOT NULL,
    collected_at DATETIME2(3) NOT NULL
  );
END;
