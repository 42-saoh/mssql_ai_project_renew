CREATE TABLE codex_runs (
  codex_run_id TEXT PRIMARY KEY,
  chat_run_id TEXT NOT NULL,
  run_type TEXT NOT NULL,
  runtime_profile TEXT NOT NULL,
  workspace_id TEXT NOT NULL,
  status TEXT NOT NULL,
  output_schema_name TEXT NOT NULL,
  validation_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
