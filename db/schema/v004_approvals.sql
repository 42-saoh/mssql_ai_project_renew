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
