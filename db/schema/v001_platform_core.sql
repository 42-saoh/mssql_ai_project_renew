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
