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
